-- Create database and user
CREATE DATABASE alumind;
CREATE USER admin WITH PASSWORD 'temp123';

-- Connect to the alumind database
\c alumind

-- Create the feedbacks table
CREATE TABLE feedbacks (
    id TEXT PRIMARY KEY,
    feedback TEXT NOT NULL,
    sentiment TEXT CHECK (sentiment IN ('POSITIVO', 'NEGATIVO', 'INCONCLUSIVO')),
    feature_code TEXT,
    feature_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Grant privileges to admin user
GRANT ALL PRIVILEGES ON DATABASE alumind TO admin;
GRANT USAGE ON SCHEMA public TO admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO admin;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public 
GRANT ALL PRIVILEGES ON TABLES TO admin;

-- Add helpful comments to the table and columns
COMMENT ON TABLE feedbacks IS 'Stores user feedback and sentiment analysis results';
COMMENT ON COLUMN feedbacks.id IS 'Unique identifier for the feedback';
COMMENT ON COLUMN feedbacks.feedback IS 'The actual feedback text from the user';
COMMENT ON COLUMN feedbacks.sentiment IS 'Sentiment analysis result (POSITIVO or NEGATIVO)';
COMMENT ON COLUMN feedbacks.feature_code IS 'Code representing the main feature request';
COMMENT ON COLUMN feedbacks.feature_reason IS 'Description of the feature request';
COMMENT ON COLUMN feedbacks.created_at IS 'Timestamp when the feedback was created';

-- Create index for common queries
CREATE INDEX idx_feedbacks_sentiment ON feedbacks(sentiment);
CREATE INDEX idx_feedbacks_created_at ON feedbacks(created_at);
CREATE INDEX idx_feedbacks_feature_code ON feedbacks(feature_code);

-- Grant schema privileges to admin
GRANT CREATE ON SCHEMA public TO admin;

-- Make sure admin owns the schema
ALTER SCHEMA public OWNER TO admin;

-- Explicitly grant all privileges on the feedbacks table
GRANT ALL PRIVILEGES ON TABLE feedbacks TO admin;