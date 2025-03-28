from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import DictCursor
import os
from dotenv import load_dotenv

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
    cur.execute('''
    CREATE TABLE IF NOT EXISTS feedbacks (
        id TEXT PRIMARY KEY,
        feedback TEXT NOT NULL,
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
    
    # Insert feedback into the database
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO feedbacks (id, feedback) VALUES (%s, %s)',
            (feedback_data['id'], feedback_data['feedback'])
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'Feedback received successfully'}), 201
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
