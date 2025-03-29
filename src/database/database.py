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
        feature_code TEXT,
        feature_reason TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    cur.close()
    conn.close()