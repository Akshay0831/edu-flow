"""
Initial Database Schema Migration

This migration sets up the basic database schema for Edu-Flow:
- User authentication and profile tables/collections
- Course management structure
- Student enrollment system
- Basic relationships and indexes

Author: Edu-Flow Team
"""

# Migration metadata
VERSION = "1.0.0"
NAME = "Initial Schema"
DESCRIPTION = """Create initial database schema for Edu-Flow application"""

# SQL Migration (for SQL databases)
UPGRADE_SQL = """
-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'teacher', 'student')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    provider VARCHAR(20) DEFAULT 'jwt'
);

-- User profiles table
CREATE TABLE IF NOT EXISTS user_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    phone VARCHAR(20),
    address TEXT,
    avatar_url VARCHAR(255),
    date_of_birth DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Courses table
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    credits INTEGER NOT NULL CHECK (credits > 0),
    department_id INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'archived')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments (id)
);

-- Departments table
CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Students table
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    student_id VARCHAR(20) UNIQUE NOT NULL,
    grade_level INTEGER CHECK (grade_level BETWEEN 9 AND 12),
    enrollment_date DATE NOT NULL,
    graduation_date DATE,
    gpa DECIMAL(3,2) DEFAULT 0.00,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'graduated', 'transferred', 'suspended', 'withdrawn')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Teachers table
CREATE TABLE IF NOT EXISTS teachers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    teacher_id VARCHAR(20) UNIQUE NOT NULL,
    department_id INTEGER NOT NULL,
    hire_date DATE NOT NULL,
    qualification VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments (id)
);

-- Enrollments table
CREATE TABLE IF NOT EXISTS enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    enrollment_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'dropped', 'completed', 'failed')),
    final_grade VARCHAR(2),
    credits_earned INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE,
    UNIQUE (student_id, course_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_provider ON users(provider);

CREATE INDEX IF NOT EXISTS idx_courses_code ON courses(code);
CREATE INDEX IF NOT EXISTS idx_courses_department ON courses(department_id);
CREATE INDEX IF NOT EXISTS idx_courses_status ON courses(status);

CREATE INDEX IF NOT EXISTS idx_departments_code ON departments(code);
CREATE INDEX IF NOT EXISTS idx_departments_name ON departments(name);

CREATE INDEX IF NOT EXISTS idx_students_user_id ON students(user_id);
CREATE INDEX IF NOT EXISTS idx_students_student_id ON students(student_id);
CREATE INDEX IF NOT EXISTS idx_students_grade_level ON students(grade_level);
CREATE INDEX IF NOT EXISTS idx_students_status ON students(status);

CREATE INDEX IF NOT EXISTS idx_teachers_user_id ON teachers(user_id);
CREATE INDEX IF NOT EXISTS idx_teachers_teacher_id ON teachers(teacher_id);
CREATE INDEX IF NOT EXISTS idx_teachers_department ON teachers(department_id);

CREATE INDEX IF NOT EXISTS idx_enrollments_student_id ON enrollments(student_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_course_id ON enrollments(course_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_status ON enrollments(status);
"""

DOWNGRADE_SQL = """
-- Drop indexes
DROP INDEX IF EXISTS idx_enrollments_status;
DROP INDEX IF EXISTS idx_enrollments_course_id;
DROP INDEX IF EXISTS idx_enrollments_student_id;
DROP INDEX IF EXISTS idx_teachers_department;
DROP INDEX IF EXISTS idx_teachers_teacher_id;
DROP INDEX IF EXISTS idx_teachers_user_id;
DROP INDEX IF EXISTS idx_students_status;
DROP INDEX IF EXISTS idx_students_grade_level;
DROP INDEX IF EXISTS idx_students_student_id;
DROP INDEX IF EXISTS idx_students_user_id;
DROP INDEX IF EXISTS idx_departments_name;
DROP INDEX IF EXISTS idx_departments_code;
DROP INDEX IF EXISTS idx_courses_status;
DROP INDEX IF EXISTS idx_courses_department;
DROP INDEX IF EXISTS idx_courses_code;
DROP INDEX IF EXISTS idx_users_provider;
DROP INDEX IF EXISTS idx_users_is_active;
DROP INDEX IF EXISTS idx_users_role;
DROP INDEX IF EXISTS idx_users_email;

-- Drop tables
DROP TABLE IF EXISTS enrollments;
DROP TABLE IF EXISTS teachers;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS departments;
DROP TABLE IF EXISTS user_profiles;
DROP TABLE IF EXISTS users;
"""

# MongoDB Migration (for MongoDB databases)
UPGRADE_MONGO = {
    "operation": "create_collections",
    "collections": [
        {
            "name": "users",
            "indexes": [
                {"key": {"email": 1}, "unique": True},
                {"key": {"role": 1}},
                {"key": {"is_active": 1}},
                {"key": {"provider": 1}},
                {"key": {"created_at": 1}}
            ]
        },
        {
            "name": "user_profiles",
            "indexes": [
                {"key": {"user_id": 1}, "unique": True},
                {"key": {"created_at": 1}}
            ]
        },
        {
            "name": "courses",
            "indexes": [
                {"key": {"code": 1}, "unique": True},
                {"key": {"department_id": 1}},
                {"key": {"status": 1}},
                {"key": {"created_at": 1}}
            ]
        },
        {
            "name": "departments",
            "indexes": [
                {"key": {"code": 1}, "unique": True},
                {"key": {"name": 1}},
                {"key": {"created_at": 1}}
            ]
        },
        {
            "name": "students",
            "indexes": [
                {"key": {"user_id": 1}, "unique": True},
                {"key": {"student_id": 1}, "unique": True},
                {"key": {"grade_level": 1}},
                {"key": {"status": 1}},
                {"key": {"created_at": 1}}
            ]
        },
        {
            "name": "teachers",
            "indexes": [
                {"key": {"user_id": 1}, "unique": True},
                {"key": {"teacher_id": 1}, "unique": True},
                {"key": {"department_id": 1}},
                {"key": {"created_at": 1}}
            ]
        },
        {
            "name": "enrollments",
            "indexes": [
                {"key": {"student_id": 1}},
                {"key": {"course_id": 1}},
                {"key": {"status": 1}},
                {"key": {"created_at": 1}},
                {"unique": True, "key": {"student_id": 1, "course_id": 1}}
            ]
        }
    ]
}

DOWNGRADE_MONGO = {
    "operation": "drop_collections",
    "collections": ["enrollments", "teachers", "students", "departments", "courses", "user_profiles", "users"]
}

# Python Migration (for complex operations)
async def upgrade_migration(database):
    """
    Custom upgrade logic for complex migrations.
    Use this when SQL or MongoDB operations are insufficient.
    """
    # Insert default departments
    default_departments = [
        {"code": "CS", "name": "Computer Science", "description": "Computer Science Department"},
        {"code": "MATH", "name": "Mathematics", "description": "Mathematics Department"},
        {"code": "SCI", "name": "Science", "description": "Science Department"},
        {"code": "ENG", "name": "English", "description": "English Department"},
        {"code": "HIST", "name": "History", "description": "History Department"}
    ]
    
    for dept in default_departments:
        try:
            await database.insert_one("departments", dept)
        except Exception as e:
            # Department might already exist
            if "duplicate key" not in str(e).lower():
                logger.error(f"Failed to insert department {dept['code']}: {e}")

async def downgrade_migration(database):
    """
    Custom downgrade logic for complex migrations.
    Use this when SQL or MongoDB operations are insufficient.
    """
    # Clean up any remaining data
    await database.delete_many("enrollments", {})
    await database.delete_many("teachers", {})
    await database.delete_many("students", {})
    await database.delete_many("courses", {})
    await database.delete_many("departments", {})
    await database.delete_many("user_profiles", {})
    await database.delete_many("users", {})