from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import DictCursor
import os
from dotenv import load_dotenv
from core_functions import *

# Load environment variables
load_dotenv()

app = Flask(__name__)

CORS(app)

# Database setup
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
    # Update feedbacks table to include sentiment
    cur.execute('''
    CREATE TABLE IF NOT EXISTS feedbacks (
        id TEXT PRIMARY KEY,
        feedback TEXT NOT NULL,
        sentiment TEXT CHECK (sentiment IN ('POSITIVO', 'NEGATIVO')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    cur.close()
    conn.close()

# Initialize the database on startup
init_db()

# Create feedback endpoint
@app.route('/feedbacks', methods=['POST'])
def create_feedback():
    if not request.json or 'id' not in request.json or 'feedback' not in request.json:
        return jsonify({'error': 'Invalid request data'}), 400
    
    feedback_data = {
        'id': request.json['id'],
        'feedback': request.json['feedback']
    }
    
    try:
        # Analyze feedback using LLM
        if spam_filter(feedback_data['feedback']):
            analysis_result = analyze_feedback_langchain(feedback_data['feedback'], feedback_data['id'])
        else:
            return jsonify({'error': 'Feedback is spam'}), 400
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Insert main feedback with sentiment
        cur.execute(
            'INSERT INTO feedbacks (id, feedback, sentiment) VALUES (%s, %s, %s)',
            (feedback_data['id'], feedback_data['feedback'], analysis_result['sentiment'])
        )
        
        # Insert requested features
        for feature in analysis_result['requested_features']:
            cur.execute(
                'INSERT INTO requested_features (feedback_id, feature_code, reason) VALUES (%s, %s, %s)',
                (feedback_data['id'], feature['code'], feature['reason'])
            )
        
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'Feedback processed and stored successfully'}), 201
    except psycopg2.IntegrityError:
        return jsonify({'error': 'Feedback with this ID already exists'}), 409
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    app.run(debug=True)
