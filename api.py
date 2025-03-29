from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from core_functions import *
import threading

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

app = Flask(__name__)

CORS(app)

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

# Dashboard endpoint
@app.route('/dashboard', methods=['GET'])
def dashboard():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    
    # Query to get count of feedbacks by sentiment
    cur.execute("SELECT sentiment, COUNT(*) as count FROM feedbacks GROUP BY sentiment;")
    sentiment_data = cur.fetchall()
    sentiment_summary = [{'sentiment': row['sentiment'], 'count': row['count']} for row in sentiment_data]
    
    # Query to get a detailed list of feedbacks (ordered by creation time)
    cur.execute("SELECT id, feedback, sentiment, created_at FROM feedbacks ORDER BY created_at DESC;")
    feedbacks = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template("dashboard.html", sentiment_summary=sentiment_summary, feedbacks=feedbacks)


if __name__ == '__main__':
    # Start the scheduler in a separate thread
    scheduler_thread = threading.Thread(target=schedule_weekly_report)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    # Run the Flask app
    app.run(debug=True)
