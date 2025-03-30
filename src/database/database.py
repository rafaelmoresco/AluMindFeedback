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
        sentiment TEXT CHECK (sentiment IN ('POSITIVO', 'NEGATIVO', 'INCONCLUSIVO')),
        feature_code TEXT,
        feature_reason TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    cur.close()
    conn.close()

# Function to insert feedback
def insert_feedback(feedback_data):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        'INSERT INTO feedbacks (id, feedback, sentiment, feature_code, feature_reason) VALUES (%s, %s, %s, %s, %s)',
        (
            feedback_data['id'],
            feedback_data['feedback'],
            feedback_data['sentiment'],
            feedback_data.get('feature_code'),
            feedback_data.get('feature_reason')
        )
    )
    
    conn.commit()
    cur.close()
    conn.close()

# Function to get total feedback count
def get_total_feedback_count():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    
    cur.execute("SELECT COUNT(*) as total FROM feedbacks;")
    total_feedbacks = cur.fetchone()['total']
    
    cur.close()
    conn.close()
    return total_feedbacks

# Function to get sentiment data
def get_sentiment_data():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    
    cur.execute("""
        SELECT 
            sentiment, 
            COUNT(*) as count,
            CAST((COUNT(*)::float * 100 / NULLIF((SELECT COUNT(*) FROM feedbacks), 0)) AS DECIMAL(5,1)) as percentage
        FROM feedbacks 
        GROUP BY sentiment;
    """)
    sentiment_data = cur.fetchall()
    
    cur.close()
    conn.close()
    return sentiment_data

# Function to get top requested features
def get_top_requested_features():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    
    cur.execute("""
        SELECT 
            feature_code,
            COUNT(*) as count_value
        FROM feedbacks 
        WHERE feature_code IS NOT NULL
        GROUP BY feature_code
        ORDER BY count_value DESC
        LIMIT 3;
    """)
    top_features = cur.fetchall()
    
    cur.close()
    conn.close()
    return top_features

# Function to get detailed feedbacks
def get_detailed_feedbacks():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    
    cur.execute("""
        SELECT id, feedback, sentiment, feature_code, feature_reason, created_at 
        FROM feedbacks 
        ORDER BY created_at DESC;
    """)
    feedbacks = cur.fetchall()
    
    cur.close()
    conn.close()
    return feedbacks

# Function to get feature reason by feature code
def get_feature_reason(feature_code):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    
    cur.execute("""
        SELECT feature_reason 
        FROM feedbacks 
        WHERE feature_code = %s 
        LIMIT 1;
    """, (feature_code,))
    feature_reason_row = cur.fetchone()
    
    cur.close()
    conn.close()
    return feature_reason_row['feature_reason'] if feature_reason_row else None