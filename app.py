from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from db_config import get_db_connection
from datetime import date

app = Flask(__name__)
app.secret_key = "feedback_system_secret_key_2026"


def db():
    return get_db_connection()


def login_required():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return None


def role_required(role):
    check = login_required()
    if check:
        return check

    if session["role"] != role:
        flash("Unauthorized access", "danger")
        return redirect(url_for("login"))
    return None


def add_notification(user_id, title, message):
    connection = db()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO notifications (user_id, title, message) VALUES (%s, %s, %s)",
        (user_id, title, message)
    )
    connection.commit()
    cursor.close()
    connection.close()


@app.route("/")
def login():
    if "user_id" in session:
        return redirect(url_for(session["role"] + "_dashboard"))
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def do_login():
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not email or not password:
        flash("Please enter email and password", "danger")
        return redirect(url_for("login"))

    connection = db()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM users WHERE email = %s AND status = 'active'",
        (email,)
    )
    user = cursor.fetchone()
    cursor.close()
    connection.close()

    if user and check_password_hash(user["password_hash"], password):
        session["user_id"] = user["user_id"]
        session["full_name"] = user["full_name"]
        session["role"] = user["role"]
        session["department_id"] = user["department_id"]

        return redirect(url_for(user["role"] + "_dashboard"))

    flash("Invalid email or password", "danger")
    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for("login"))


@app.route("/director/dashboard")
def director_dashboard():
    check = role_required("director")
    if check:
        return check

    connection = db()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total FROM departments")
    total_departments = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM users")
    total_users = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM feedback_responses")
    total_feedback = cursor.fetchone()["total"]

    cursor.execute(
        "SELECT COUNT(*) AS total FROM issues WHERE status NOT IN ('Resolved','Closed')"
    )
    pending_issues = cursor.fetchone()["total"]

    cursor.execute(
        """SELECT d.department_name, COALESCE(AVG(f.rating_value), 0) AS avg_rating
           FROM departments d
           LEFT JOIN feedback_responses f ON d.department_id = f.department_id
           GROUP BY d.department_id"""
    )
    department_ratings = cursor.fetchall()

    cursor.execute(
        """SELECT c.category_name, COUNT(f.response_id) AS total
           FROM feedback_categories c
           LEFT JOIN feedback_responses f ON c.category_id = f.category_id
           GROUP BY c.category_id"""
    )
    category_counts = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "director_dashboard.html",
        total_departments=total_departments,
        total_users=total_users,
        total_feedback=total_feedback,
        pending_issues=pending_issues,
        department_ratings=department_ratings,
        category_counts=category_counts
    )


@app.route("/hod/dashboard")
def hod_dashboard():
    check = role_required("hod")
    if check:
        return check

    department_id = session["department_id"]

    connection = db()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        "SELECT COUNT(*) AS total FROM faculty f JOIN users u ON f.user_id=u.user_id WHERE u.department_id=%s",
        (department_id,)
    )
    total_faculty = cursor.fetchone()["total"]

    cursor.execute(
        "SELECT COUNT(*) AS total FROM students s JOIN users u ON s.user_id=u.user_id WHERE u.department_id=%s",
        (department_id,)
    )
    total_students = cursor.fetchone()["total"]

    cursor.execute(
        "SELECT COUNT(*) AS total FROM feedback_responses WHERE department_id=%s",
        (department_id,)
    )
    total_feedback = cursor.fetchone()["total"]

    cursor.execute(
        """SELECT COUNT(*) AS total FROM issues
           WHERE department_id=%s AND status NOT IN ('Resolved','Closed')""",
        (department_id,)
    )
    pending_issues = cursor.fetchone()["total"]

    cursor.execute(
        """SELECT c.category_name, COALESCE(AVG(f.rating_value),0) AS avg_rating
           FROM feedback_categories c
           LEFT JOIN feedback_responses f
           ON c.category_id=f.category_id AND f.department_id=%s
           GROUP BY c.category_id""",
        (department_id,)
    )
    category_ratings = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "hod_dashboard.html",
        total_faculty=total_faculty,
        total_students=total_students,
        total_feedback=total_feedback,
        pending_issues=pending_issues,
        category_ratings=category_ratings
    )


@app.route("/faculty/dashboard")
def faculty_dashboard():
    check = role_required("faculty")
    if check:
        return check

    connection = db()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        "SELECT faculty_id FROM faculty WHERE user_id=%s",
        (session["user_id"],)
    )
    faculty = cursor.fetchone()

    faculty_id = faculty["faculty_id"] if faculty else 0

    cursor.execute(
        "SELECT COUNT(*) AS total FROM feedback_responses WHERE faculty_id=%s",
        (faculty_id,)
    )
    total_feedback = cursor.fetchone()["total"]

    cursor.execute(
        """SELECT COALESCE(AVG(rating_value),0) AS avg_rating
           FROM feedback_responses WHERE faculty_id=%s""",
        (faculty_id,)
    )
    average_rating = cursor.fetchone()["avg_rating"]

    cursor.execute(
        """SELECT COUNT(*) AS total FROM issues WHERE assigned_to=%s
           AND status NOT IN ('Resolved','Closed')""",
        (faculty_id,)
    )
    assigned_issues = cursor.fetchone()["total"]

    cursor.close()
    connection.close()

    return render_template(
        "faculty_dashboard.html",
        total_feedback=total_feedback,
        average_rating=round(float(average_rating), 2),
        assigned_issues=assigned_issues
    )


@app.route("/student/dashboard")
def student_dashboard():
    check = role_required("student")
    if check:
        return check

    connection = db()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM students WHERE user_id=%s",
        (session["user_id"],)
    )
    student = cursor.fetchone()

    cursor.execute(
        "SELECT COUNT(*) AS total FROM feedback_participation WHERE student_id=%s",
        (student["student_id"] if student else 0,)
    )
    submitted_feedback = cursor.fetchone()["total"]

    cursor.execute(
        """SELECT COUNT(*) AS total FROM notifications
           WHERE user_id=%s AND is_read=0""",
        (session["user_id"],)
    )
    unread_notifications = cursor.fetchone()["total"]

    cursor.close()
    connection.close()

    return render_template(
        "student_dashboard.html",
        student=student,
        submitted_feedback=submitted_feedback,
        unread_notifications=unread_notifications
    )


@app.route("/director/departments", methods=["GET", "POST"])
def manage_departments():
    check = role_required("director")
    if check:
        return check

    connection = db()
    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":
        department_name = request.form.get("department_name", "").strip()

        if department_name:
            cursor.execute(
                "INSERT INTO departments (department_name) VALUES (%s)",
                (department_name,)
            )
            connection.commit()
            flash("Department added successfully", "success")

    cursor.execute("SELECT * FROM departments ORDER BY department_id")
    departments = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("manage_departments.html", departments=departments)


@app.route("/director/users", methods=["GET", "POST"])
def manage_users():
    check = role_required("director")
    if check:
        return check

    connection = db()
    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role")
        department_id = request.form.get("department_id") or None

        if full_name and email and password and role:
            cursor.execute(
                "SELECT user_id FROM users WHERE email=%s",
                (email,)
            )
            existing = cursor.fetchone()

            if existing:
                flash("Email already exists", "danger")
            else:
                password_hash = generate_password_hash(password)

                cursor.execute(
                    """INSERT INTO users
                    (full_name,email,password_hash,role,department_id)
                    VALUES (%s,%s,%s,%s,%s)""",
                    (full_name, email, password_hash, role, department_id)
                )
                user_id = cursor.lastrowid

                if role == "faculty":
                    cursor.execute(
                        "INSERT INTO faculty (user_id, employee_code, designation) VALUES (%s,%s,%s)",
                        (user_id, request.form.get("employee_code", ""), request.form.get("designation", ""))
                    )

                if role == "student":
                    cursor.execute(
                        """INSERT INTO students
                        (user_id, roll_no, year, semester, section)
                        VALUES (%s,%s,%s,%s,%s)""",
                        (
                            user_id,
                            request.form.get("roll_no", ""),
                            request.form.get("year", 1),
                            request.form.get("semester", 1),
                            request.form.get("section", "A")
                        )
                    )

                connection.commit()
                flash("User created successfully", "success")

    cursor.execute("SELECT * FROM departments")
    departments = cursor.fetchall()

    cursor.execute(
        """SELECT u.*, d.department_name
           FROM users u
           LEFT JOIN departments d ON u.department_id=d.department_id
           ORDER BY u.user_id DESC"""
    )
    users = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("manage_users.html", departments=departments, users=users)


@app.route("/director/categories", methods=["GET", "POST"])
def manage_categories():
    check = role_required("director")
    if check:
        return check

    connection = db()
    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":
        category_name = request.form.get("category_name", "").strip()

        if category_name:
            cursor.execute(
                "INSERT INTO feedback_categories (category_name) VALUES (%s)",
                (category_name,)
            )
            connection.commit()
            flash("Category added", "success")

    cursor.execute("SELECT * FROM feedback_categories")
    categories = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("manage_categories.html", categories=categories)


@app.route("/director/questions", methods=["GET", "POST"])
def manage_questions():
    check = role_required("director")
    if check:
        return check

    connection = db()
    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":
        category_id = request.form.get("category_id")
        question_text = request.form.get("question_text", "").strip()
        question_type = request.form.get("question_type")

        if category_id and question_text and question_type:
            cursor.execute(
                """INSERT INTO questions
                (category_id, question_text, question_type)
                VALUES (%s,%s,%s)""",
                (category_id, question_text, question_type)
            )
            connection.commit()
            flash("Question added", "success")

    cursor.execute("SELECT * FROM feedback_categories")
    categories = cursor.fetchall()

    cursor.execute(
        """SELECT q.*, c.category_name
           FROM questions q
           JOIN feedback_categories c ON q.category_id=c.category_id
           ORDER BY q.question_id DESC"""
    )
    questions = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("manage_questions.html", categories=categories, questions=questions)


@app.route("/director/cycles", methods=["GET", "POST"])
def manage_cycles():
    check = role_required("director")
    if check:
        return check

    connection = db()
    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        department_id = request.form.get("department_id") or None
        semester = request.form.get("semester") or None
        academic_year = request.form.get("academic_year", "")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")

        if title and start_date and end_date:
            cursor.execute(
                """INSERT INTO feedback_cycles
                (title,department_id,semester,academic_year,start_date,end_date,status,created_by)
                VALUES (%s,%s,%s,%s,%s,%s,'active',%s)""",
                (title, department_id, semester, academic_year, start_date, end_date, session["user_id"])
            )
            connection.commit()
            flash("Feedback cycle created", "success")

    cursor.execute("SELECT * FROM departments")
    departments = cursor.fetchall()

    cursor.execute(
        """SELECT fc.*, d.department_name
           FROM feedback_cycles fc
           LEFT JOIN departments d ON fc.department_id=d.department_id
           ORDER BY fc.cycle_id DESC"""
    )
    cycles = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("manage_cycles.html", departments=departments, cycles=cycles)


@app.route("/hod/faculty", methods=["GET", "POST"])
def manage_faculty():
    check = role_required("hod")
    if check:
        return check

    department_id = session["department_id"]
    connection = db()
    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        employee_code = request.form.get("employee_code", "")
        designation = request.form.get("designation", "")

        if full_name and email and password:
            cursor.execute(
                "SELECT user_id FROM users WHERE email=%s",
                (email,)
            )
            existing = cursor.fetchone()

            if existing:
                flash("Email already exists", "danger")
            else:
                password_hash = generate_password_hash(password)

                cursor.execute(
                    """INSERT INTO users
                    (full_name,email,password_hash,role,department_id)
                    VALUES (%s,%s,%s,'faculty',%s)""",
                    (full_name, email, password_hash, department_id)
                )
                user_id = cursor.lastrowid

                cursor.execute(
                    "INSERT INTO faculty (user_id,employee_code,designation) VALUES (%s,%s,%s)",
                    (user_id, employee_code, designation)
                )

                connection.commit()
                flash("Faculty added successfully", "success")

    cursor.execute(
        """SELECT u.*, f.employee_code, f.designation
           FROM users u
           JOIN faculty f ON u.user_id=f.user_id
           WHERE u.department_id=%s""",
        (department_id,)
    )
    faculty_list = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("manage_faculty.html", faculty_list=faculty_list)


@app.route("/hod/students", methods=["GET", "POST"])
def manage_students():
    check = role_required("hod")
    if check:
        return check

    department_id = session["department_id"]
    connection = db()
    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        roll_no = request.form.get("roll_no", "")
        year = request.form.get("year", 1)
        semester = request.form.get("semester", 1)
        section = request.form.get("section", "A")

        if full_name and email and password:
            cursor.execute(
                "SELECT user_id FROM users WHERE email=%s",
                (email,)
            )
            existing = cursor.fetchone()

            if existing:
                flash("Email already exists", "danger")
            else:
                password_hash = generate_password_hash(password)

                cursor.execute(
                    """INSERT INTO users
                    (full_name,email,password_hash,role,department_id)
                    VALUES (%s,%s,%s,'student',%s)""",
                    (full_name, email, password_hash, department_id)
                )
                user_id = cursor.lastrowid

                cursor.execute(
                    """INSERT INTO students
                    (user_id,roll_no,year,semester,section)
                    VALUES (%s,%s,%s,%s,%s)""",
                    (user_id, roll_no, year, semester, section)
                )

                connection.commit()
                flash("Student added successfully", "success")

    cursor.execute(
        """SELECT u.*, s.roll_no, s.year, s.semester, s.section
           FROM users u
           JOIN students s ON u.user_id=s.user_id
           WHERE u.department_id=%s""",
        (department_id,)
    )
    students = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("manage_students.html", students=students)


@app.route("/student/submit-feedback", methods=["GET", "POST"])
def submit_feedback():
    check = role_required("student")
    if check:
        return check

    connection = db()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM students WHERE user_id=%s",
        (session["user_id"],)
    )
    student = cursor.fetchone()

    if not student:
        flash("Student profile not found", "danger")
        return redirect(url_for("student_dashboard"))

    cursor.execute(
        """SELECT * FROM feedback_cycles
           WHERE status='active'
           AND CURDATE() BETWEEN start_date AND end_date
           AND (department_id IS NULL OR department_id=%s)""",
        (session["department_id"],)
    )
    cycles = cursor.fetchall()

    cursor.execute("SELECT * FROM feedback_categories")
    categories = cursor.fetchall()

    cursor.execute("SELECT * FROM faculty")
    faculty_list = cursor.fetchall()

    if request.method == "POST":
        cycle_id = request.form.get("cycle_id")
        category_id = request.form.get("category_id")
        faculty_id = request.form.get("faculty_id") or None
        rating = request.form.get("rating")
        yes_no = request.form.get("yes_no")
        suggestion = request.form.get("suggestion", "").strip()

        if not cycle_id or not category_id:
            flash("Please select feedback cycle and category", "danger")
            return redirect(url_for("submit_feedback"))

        cursor.execute(
            """SELECT participation_id FROM feedback_participation
               WHERE cycle_id=%s AND student_id=%s""",
            (cycle_id, student["student_id"])
        )
        already = cursor.fetchone()

        if already:
            flash("You have already submitted feedback for this cycle", "warning")
        else:
            cursor.execute(
                "INSERT INTO feedback_participation (cycle_id,student_id) VALUES (%s,%s)",
                (cycle_id, student["student_id"])
            )

            cursor.execute(
                "SELECT department_id FROM feedback_cycles WHERE cycle_id=%s",
                (cycle_id,)
            )
            cycle = cursor.fetchone()
            department_id = cycle["department_id"] or session["department_id"]

            cursor.execute(
                """INSERT INTO feedback_responses
                (cycle_id,department_id,category_id,faculty_id,question_id,rating_value,yes_no_value,text_response)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    cycle_id, department_id, category_id, faculty_id, 1,
                    rating, yes_no, suggestion
                )
            )

            connection.commit()

            add_notification(
                session["user_id"],
                "Feedback Submitted",
                "Your feedback has been submitted successfully."
            )

            flash("Feedback submitted successfully", "success")
            return redirect(url_for("student_dashboard"))

    cursor.close()
    connection.close()

    return render_template(
        "submit_feedback.html",
        cycles=cycles,
        categories=categories,
        faculty_list=faculty_list
    )


@app.route("/student/feedback-status")
def feedback_status():
    check = role_required("student")
    if check:
        return check

    connection = db()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        "SELECT student_id FROM students WHERE user_id=%s",
        (session["user_id"],)
    )
    student = cursor.fetchone()

    if not student:
        flash("Student profile not found", "danger")
        return redirect(url_for("student_dashboard"))

    student_id = student["student_id"]

    cursor.execute(
        """SELECT fc.title, fp.submitted_at
           FROM feedback_participation fp
           JOIN feedback_cycles fc ON fp.cycle_id=fc.cycle_id
           WHERE fp.student_id=%s
           ORDER BY fp.submitted_at DESC""",
        (student_id,)
    )
    submissions = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("feedback_status.html", submissions=submissions)



@app.route("/hod/issues", methods=["GET", "POST"])
def manage_issues():
    check = role_required("hod")
    if check:
        return check

    department_id = session["department_id"]
    connection = db()
    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":
        issue_id = request.form.get("issue_id")
        status = request.form.get("status")
        action_taken = request.form.get("action_taken", "")
        priority = request.form.get("priority")

        resolved_at = date.today() if status in ("Resolved", "Closed") else None

        cursor.execute(
            """UPDATE issues
               SET status=%s, action_taken=%s, priority=%s, resolved_at=%s
               WHERE issue_id=%s AND department_id=%s""",
            (status, action_taken, priority, resolved_at, issue_id, department_id)
        )
        connection.commit()
        flash("Issue updated successfully", "success")

    cursor.execute(
        """SELECT i.*, c.category_name
           FROM issues i
           JOIN feedback_categories c ON i.category_id=c.category_id
           WHERE i.department_id=%s
           ORDER BY FIELD(i.priority,'Critical','High','Medium','Low'), i.created_at DESC""",
        (department_id,)
    )
    issues = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("manage_issues.html", issues=issues)


@app.route("/faculty/feedback")
def faculty_feedback():
    check = role_required("faculty")
    if check:
        return check

    connection = db()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        "SELECT faculty_id FROM faculty WHERE user_id=%s",
        (session["user_id"],)
    )
    faculty = cursor.fetchone()
    faculty_id = faculty["faculty_id"] if faculty else 0

    cursor.execute(
        """SELECT f.rating_value, f.yes_no_value, f.text_response,
                  c.category_name, fc.title
           FROM feedback_responses f
           JOIN feedback_categories c ON f.category_id=c.category_id
           JOIN feedback_cycles fc ON f.cycle_id=fc.cycle_id
           WHERE f.faculty_id=%s
           ORDER BY f.submitted_at DESC""",
        (faculty_id,)
    )
    feedback_list = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("faculty_feedback.html", feedback_list=feedback_list)


@app.route("/faculty/issues", methods=["GET", "POST"])
def faculty_issues():
    check = role_required("faculty")
    if check:
        return check

    connection = db()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        "SELECT faculty_id FROM faculty WHERE user_id=%s",
        (session["user_id"],)
    )
    faculty = cursor.fetchone()
    faculty_id = faculty["faculty_id"] if faculty else 0

    if request.method == "POST":
        issue_id = request.form.get("issue_id")
        status = request.form.get("status")
        action_taken = request.form.get("action_taken", "")

        cursor.execute(
            """UPDATE issues SET status=%s, action_taken=%s
               WHERE issue_id=%s AND assigned_to=%s""",
            (status, action_taken, issue_id, faculty_id)
        )
        connection.commit()
        flash("Issue updated", "success")

    cursor.execute(
        """SELECT i.*, c.category_name
           FROM issues i
           JOIN feedback_categories c ON i.category_id=c.category_id
           WHERE i.assigned_to=%s""",
        (faculty_id,)
    )
    issues = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("faculty_issues.html", issues=issues)


@app.route("/director/reports")
@app.route("/hod/reports")
def reports():
    check = role_required(session["role"])
    if check:
        return check

    department_id = session["department_id"] if session["role"] == "hod" else None

    connection = db()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT d.department_name, c.category_name,
               COUNT(f.response_id) AS total_responses,
               COALESCE(AVG(f.rating_value),0) AS average_rating,
               SUM(CASE WHEN f.yes_no_value='Yes' THEN 1 ELSE 0 END) AS yes_count,
               SUM(CASE WHEN f.yes_no_value='No' THEN 1 ELSE 0 END) AS no_count
        FROM feedback_responses f
        JOIN departments d ON f.department_id=d.department_id
        JOIN feedback_categories c ON f.category_id=c.category_id
    """

    params = ()

    if department_id:
        query += " WHERE f.department_id=%s"
        params = (department_id,)

    query += """
        GROUP BY d.department_id, c.category_id
        ORDER BY d.department_name, c.category_name
    """

    cursor.execute(query, params)
    report_data = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("reports.html", report_data=report_data)


@app.route("/director/comparison-report")
def comparison_report():
    check = role_required("director")
    if check:
        return check

    connection = db()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT * FROM feedback_cycles ORDER BY cycle_id DESC")
    cycles = cursor.fetchall()

    current_cycle_id = request.args.get("current_cycle_id", type=int)
    previous_cycle_id = request.args.get("previous_cycle_id", type=int)

    if not current_cycle_id or not previous_cycle_id:
        current_cycle_id = cycles[0]["cycle_id"] if cycles else None
        previous_cycle_id = cycles[1]["cycle_id"] if len(cycles) > 1 else None

    current_summary = None
    previous_summary = None
    comparison = []
    improvement = 0

    same_cycle = False

    if current_cycle_id and previous_cycle_id and current_cycle_id == previous_cycle_id:
        same_cycle = True

    if current_cycle_id and previous_cycle_id and not same_cycle:
        cursor.execute(
            """SELECT
               COUNT(*) AS total_responses,
               ROUND(AVG(rating_value),2) AS average_rating
               FROM feedback_responses
               WHERE cycle_id=%s""",
            (current_cycle_id,)
        )
        current_summary = cursor.fetchone()

        cursor.execute(
            """SELECT
               COUNT(*) AS total_responses,
               ROUND(AVG(rating_value),2) AS average_rating
               FROM feedback_responses
               WHERE cycle_id=%s""",
            (previous_cycle_id,)
        )
        previous_summary = cursor.fetchone()

        cursor.execute(
            """SELECT
               c.category_name,
               ROUND(AVG(CASE WHEN fr.cycle_id=%s THEN fr.rating_value END),2) AS current_rating,
               ROUND(AVG(CASE WHEN fr.cycle_id=%s THEN fr.rating_value END),2) AS previous_rating
               FROM feedback_categories c
               LEFT JOIN feedback_responses fr ON c.category_id=fr.category_id
               GROUP BY c.category_id, c.category_name
               ORDER BY c.category_id""",
            (current_cycle_id, previous_cycle_id)
        )
        comparison = cursor.fetchall()

        if current_summary["average_rating"] and previous_summary["average_rating"]:
            improvement = round(
                (
                    (current_summary["average_rating"] - previous_summary["average_rating"])
                    / previous_summary["average_rating"]
                ) * 100, 2
            )

    cursor.close()
    connection.close()

    return render_template(
        "comparison_report.html",
        cycles=cycles,
        current_cycle_id=current_cycle_id,
        previous_cycle_id=previous_cycle_id,
        current_summary=current_summary,
        previous_summary=previous_summary,
        comparison=comparison,
        improvement=improvement,
        same_cycle=same_cycle
    )


@app.route("/director/export-report")
def export_report():
    check = role_required("director")
    if check:
        return check

    connection = db()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT d.department_name, c.category_name,
               COUNT(f.response_id) AS total_responses,
               COALESCE(AVG(f.rating_value),0) AS average_rating,
               SUM(CASE WHEN f.yes_no_value='Yes' THEN 1 ELSE 0 END) AS yes_count,
               SUM(CASE WHEN f.yes_no_value='No' THEN 1 ELSE 0 END) AS no_count
        FROM feedback_responses f
        JOIN departments d ON f.department_id=d.department_id
        JOIN feedback_categories c ON f.category_id=c.category_id
        GROUP BY d.department_id, c.category_id
        ORDER BY d.department_name, c.category_name
    """

    cursor.execute(query)
    report_data = cursor.fetchall()

    cursor.close()
    connection.close()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Department", "Category", "Total Responses",
        "Average Rating", "Yes", "No"
    ])

    for row in report_data:
        writer.writerow([
            row["department_name"],
            row["category_name"],
            row["total_responses"],
            row["average_rating"],
            row["yes_count"],
            row["no_count"]
        ])

    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name="feedback_report.csv"
    )


@app.route("/hod/top-attendance")
def top_attendance():
    check = role_required("hod")
    if check:
        return check

    department_id = session["department_id"]

    connection = db()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """SELECT u.full_name, s.roll_no, s.year, s.semester,
                  AVG(a.percentage) AS attendance_percentage
           FROM attendance a
           JOIN students s ON a.student_id=s.student_id
           JOIN users u ON s.user_id=u.user_id
           WHERE u.department_id=%s
           GROUP BY s.student_id
           ORDER BY attendance_percentage DESC
           LIMIT 10""",
        (department_id,)
    )
    students = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("top_attendance.html", students=students)


@app.route("/hod/toppers")
def toppers():
    check = role_required("hod")
    if check:
        return check

    department_id = session["department_id"]

    connection = db()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """SELECT u.full_name, s.roll_no, s.year, s.semester,
                  SUM(m.marks_obtained) AS total_marks,
                  SUM(m.total_marks) AS maximum_marks,
                  ROUND((SUM(m.marks_obtained)/SUM(m.total_marks))*100,2) AS percentage
           FROM marks m
           JOIN students s ON m.student_id=s.student_id
           JOIN users u ON s.user_id=u.user_id
           WHERE u.department_id=%s
           GROUP BY s.student_id
           ORDER BY percentage DESC
           LIMIT 10""",
        (department_id,)
    )
    toppers_list = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("toppers.html", toppers_list=toppers_list)


@app.route("/notifications")
def notifications():
    check = login_required()
    if check:
        return check

    connection = db()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """SELECT * FROM notifications
           WHERE user_id=%s
           ORDER BY created_at DESC""",
        (session["user_id"],)
    )
    notification_list = cursor.fetchall()

    cursor.execute(
        "UPDATE notifications SET is_read=1 WHERE user_id=%s",
        (session["user_id"],)
    )
    connection.commit()

    cursor.close()
    connection.close()

    return render_template("notifications.html", notifications=notification_list)



if __name__ == "__main__":
    app.run(debug=True)
