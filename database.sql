DROP DATABASE IF EXISTS feedback_system;
CREATE DATABASE feedback_system;
USE feedback_system;

CREATE TABLE departments (
    department_id INT AUTO_INCREMENT PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('director','hod','faculty','student') NOT NULL,
    department_id INT NULL,
    status ENUM('active','inactive') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
);

CREATE TABLE faculty (
    faculty_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    employee_code VARCHAR(30) UNIQUE,
    designation VARCHAR(100),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    roll_no VARCHAR(30) UNIQUE,
    year INT NOT NULL,
    semester INT NOT NULL,
    section VARCHAR(10),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE feedback_categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE questions (
    question_id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT NOT NULL,
    question_text TEXT NOT NULL,
    question_type ENUM('yes_no','rating','text') NOT NULL,
    is_active TINYINT(1) DEFAULT 1,
    FOREIGN KEY (category_id) REFERENCES feedback_categories(category_id)
);

CREATE TABLE feedback_cycles (
    cycle_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    department_id INT NULL,
    semester INT NULL,
    academic_year VARCHAR(20),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status ENUM('active','closed') DEFAULT 'active',
    created_by INT NOT NULL,
    FOREIGN KEY (department_id) REFERENCES departments(department_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

CREATE TABLE feedback_participation (
    participation_id INT AUTO_INCREMENT PRIMARY KEY,
    cycle_id INT NOT NULL,
    student_id INT NOT NULL,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_submission (cycle_id, student_id),
    FOREIGN KEY (cycle_id) REFERENCES feedback_cycles(cycle_id),
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);

CREATE TABLE feedback_responses (
    response_id INT AUTO_INCREMENT PRIMARY KEY,
    cycle_id INT NOT NULL,
    department_id INT NOT NULL,
    category_id INT NOT NULL,
    faculty_id INT NULL,
    question_id INT NOT NULL,
    rating_value TINYINT NULL,
    yes_no_value ENUM('Yes','No') NULL,
    text_response TEXT NULL,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cycle_id) REFERENCES feedback_cycles(cycle_id),
    FOREIGN KEY (department_id) REFERENCES departments(department_id),
    FOREIGN KEY (category_id) REFERENCES feedback_categories(category_id),
    FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id),
    FOREIGN KEY (question_id) REFERENCES questions(question_id)
);

CREATE TABLE issues (
    issue_id INT AUTO_INCREMENT PRIMARY KEY,
    cycle_id INT NULL,
    department_id INT NOT NULL,
    category_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    priority ENUM('Low','Medium','High','Critical') DEFAULT 'Medium',
    assigned_to INT NULL,
    status ENUM('Submitted','Under Review','Action Required','In Progress','Resolved','Closed') DEFAULT 'Submitted',
    action_taken TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    FOREIGN KEY (department_id) REFERENCES departments(department_id),
    FOREIGN KEY (category_id) REFERENCES feedback_categories(category_id)
);

CREATE TABLE notifications (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    message TEXT NOT NULL,
    is_read TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE attendance (
    attendance_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    subject_name VARCHAR(100) NOT NULL,
    total_classes INT NOT NULL,
    attended_classes INT NOT NULL,
    percentage DECIMAL(5,2) NOT NULL,
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);

CREATE TABLE marks (
    mark_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    subject_name VARCHAR(100) NOT NULL,
    marks_obtained DECIMAL(6,2) NOT NULL,
    total_marks DECIMAL(6,2) NOT NULL,
    exam_type VARCHAR(50),
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);

INSERT INTO departments (department_name) VALUES
('Computer Science'),
('Information Technology');

INSERT INTO feedback_categories (category_name) VALUES
('Teaching & Learning'),
('Laboratory'),
('Library'),
('Curriculum'),
('Hygiene'),
('Parents'),
('Alumni'),
('Participants'),
('Teachers');

INSERT INTO questions (category_id, question_text, question_type) VALUES
(1, 'Is the teaching quality satisfactory?', 'rating'),
(1, 'Are concepts explained clearly?', 'yes_no'),
(2, 'Are laboratory facilities adequate?', 'rating'),
(3, 'Is the library resources sufficient?', 'rating'),
(4, 'Is the curriculum relevant and updated?', 'rating'),
(5, 'Is campus hygiene maintained properly?', 'yes_no'),
(6, 'Are parents receiving proper communication?', 'rating'),
(7, 'Are alumni activities helpful for students?', 'rating'),
(8, 'Are participants getting proper support?', 'rating'),
(9, 'Are teachers supportive and approachable?', 'rating');

USE feedback_system;

SELECT user_id, full_name, email, role
FROM users;