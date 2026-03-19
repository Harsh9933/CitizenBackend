-- init.sql
-- This script runs automatically when the PostgreSQL container starts for the first time.

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user'
);

CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);

-- Complaints table
CREATE TABLE IF NOT EXISTS complaints (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    latitude NUMERIC(9,6) NOT NULL,
    longitude NUMERIC(9,6) NOT NULL,
    image_url TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT complaints_status_check CHECK (
        status IN ('pending', 'verified', 'resolved')
    ),
    CONSTRAINT complaints_priority_check CHECK (
        priority IN ('low', 'medium', 'high')
    )
);

CREATE INDEX IF NOT EXISTS ix_complaints_user_id ON complaints (user_id);
CREATE INDEX IF NOT EXISTS ix_complaints_status ON complaints (status);
CREATE INDEX IF NOT EXISTS ix_complaints_priority ON complaints (priority);

-- Insert starting data
INSERT INTO users (name, email, password, role) VALUES 
('Admin User', 'admin@example.com', '$2b$12$/NBUC/SFyo5GzH9vOsttJerxjOO6b26ChCr79wyheHNKn1H9EY4Km', 'admin'),
('Standard User', 'harmishra9933@gmail.com', '$2b$12$5s/zPHLHKPB19opokdeGn.S1sX8fKudjgclyfy.klZ3LtVkCMva56', 'user')
ON CONFLICT (email) DO NOTHING;

