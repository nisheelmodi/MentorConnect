-- ============================================
-- MentorConnect Database
-- Created by: Nishil
-- ============================================

CREATE DATABASE IF NOT EXISTS mentorconnect;
USE mentorconnect;

-- ============================================
-- USERS TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fullname VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('mentor','mentee','admin') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- MENTOR PROFILE
-- ============================================

CREATE TABLE IF NOT EXISTS mentor_profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    department VARCHAR(100),
    skills TEXT,
    experience VARCHAR(100),
    bio TEXT,
    profile_image VARCHAR(255),

    FOREIGN KEY(user_id)
    REFERENCES users(id)
    ON DELETE CASCADE
);

-- ============================================
-- MENTEE PROFILE
-- ============================================

CREATE TABLE IF NOT EXISTS mentee_profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    department VARCHAR(100),
    interests TEXT,
    year VARCHAR(20),
    bio TEXT,

    FOREIGN KEY(user_id)
    REFERENCES users(id)
    ON DELETE CASCADE
);

-- ============================================
-- MENTOR REQUESTS
-- ============================================

CREATE TABLE IF NOT EXISTS mentorship_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mentor_id INT NOT NULL,
    mentee_id INT NOT NULL,

    status ENUM(
        'Pending',
        'Accepted',
        'Rejected'
    ) DEFAULT 'Pending',

    request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(mentor_id)
    REFERENCES users(id)
    ON DELETE CASCADE,

    FOREIGN KEY(mentee_id)
    REFERENCES users(id)
    ON DELETE CASCADE
);

-- ============================================
-- CHAT
-- ============================================

CREATE TABLE IF NOT EXISTS chats (
    id INT AUTO_INCREMENT PRIMARY KEY,

    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,

    message TEXT NOT NULL,

    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(sender_id)
    REFERENCES users(id)
    ON DELETE CASCADE,

    FOREIGN KEY(receiver_id)
    REFERENCES users(id)
    ON DELETE CASCADE
);

-- ============================================
-- SESSIONS
-- ============================================

CREATE TABLE IF NOT EXISTS sessions (

    id INT AUTO_INCREMENT PRIMARY KEY,

    mentor_id INT NOT NULL,

    mentee_id INT NOT NULL,

    session_date DATE,

    session_time TIME,

    meeting_link VARCHAR(255),

    status ENUM(
        'Upcoming',
        'Completed',
        'Cancelled'
    ) DEFAULT 'Upcoming',

    FOREIGN KEY(mentor_id)
    REFERENCES users(id)
    ON DELETE CASCADE,

    FOREIGN KEY(mentee_id)
    REFERENCES users(id)
    ON DELETE CASCADE
);

-- ============================================
-- FEEDBACK
-- ============================================

CREATE TABLE IF NOT EXISTS feedback (

    id INT AUTO_INCREMENT PRIMARY KEY,

    session_id INT NOT NULL,

    mentor_id INT NOT NULL,

    mentee_id INT NOT NULL,

    rating INT CHECK (rating BETWEEN 1 AND 5),

    comments TEXT,

    feedback_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(session_id)
    REFERENCES sessions(id)
    ON DELETE CASCADE,

    FOREIGN KEY(mentor_id)
    REFERENCES users(id)
    ON DELETE CASCADE,

    FOREIGN KEY(mentee_id)
    REFERENCES users(id)
    ON DELETE CASCADE
);

-- ============================================
-- ADMIN TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS admin (

    id INT AUTO_INCREMENT PRIMARY KEY,

    username VARCHAR(50) UNIQUE,

    password VARCHAR(255)
);

-- ============================================
-- DEFAULT ADMIN
-- ============================================

INSERT IGNORE INTO admin(username,password)
VALUES(
'admin',
'admin123'
);

-- ============================================
-- NOTIFICATIONS
-- ============================================

CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    type VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);