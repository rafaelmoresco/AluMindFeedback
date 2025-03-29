import os
import psycopg2
from psycopg2.extras import DictCursor

# Database connection    
def get_db_connection():
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432')
    )
    return conn

# Initialize the database
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    # Create feedbacks table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS feedbacks (
        id TEXT PRIMARY KEY,
        feedback TEXT NOT NULL,
        sentiment TEXT CHECK (sentiment IN ('POSITIVO', 'NEGATIVO')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create requested_features table first (referenced by feedbacks)
    cur.execute('''
    CREATE TABLE IF NOT EXISTS requested_features (
        id SERIAL PRIMARY KEY,
        feedback_id TEXT,
        feature_code TEXT NOT NULL,
        reason TEXT NOT NULL,
        FOREIGN KEY (feedback_id) REFERENCES feedbacks(id)
    )
    ''')
    conn.commit()
    cur.close()
    conn.close()