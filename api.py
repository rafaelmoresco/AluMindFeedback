from flask import Flask, request, jsonify, render_template, redirect
from flask_cors import CORS
from dotenv import load_dotenv
from src.utils.config import load_config
from src.database.database import *
from src.analysis.analysis import *
from src.reporting.report import schedule_weekly_report
import threading

# Load configuration
load_config()

app = Flask(__name__)

CORS(app)

# Initialize the database on startup
init_db()

# Redirect endpoint
@app.route('/')
def tohome():
    return redirect("/dashboard", code=302)

# Error handler endpoint
@app.errorhandler(404)
def page_not_found():
    return "<h1>404</h1><p>The resource could not be found.</p>", 404

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
            'INSERT INTO feedbacks (id, feedback, sentiment, feature_code, feature_reason) VALUES (%s, %s, %s, %s, %s)',
            (
                feedback_data['id'],
                feedback_data['feedback'],
                analysis_result['sentiment'],
                analysis_result.get('feature_code'),
                analysis_result.get('feature_reason')
            )
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
    
    # Get total feedback count
    cur.execute("SELECT COUNT(*) as total FROM feedbacks;")
    total_feedbacks = cur.fetchone()['total']
    
    # Query to get count of feedbacks by sentiment with percentages
    cur.execute("""
        SELECT 
            sentiment, 
            COUNT(*) as count,
            CAST((COUNT(*)::float * 100 / NULLIF((SELECT COUNT(*) FROM feedbacks), 0)) AS DECIMAL(5,1)) as percentage
        FROM feedbacks 
        GROUP BY sentiment;
    """)
    sentiment_data = cur.fetchall()
    sentiment_summary = [
        {
            'sentiment': row['sentiment'],
            'count': row['count'],
            'percentage': row['percentage']
        } for row in sentiment_data
    ]
    
    # Query to get top 3 requested features
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
    
    # Query to get a detailed list of feedbacks
    cur.execute("""
        SELECT id, feedback, sentiment, feature_code, feature_reason, created_at 
        FROM feedbacks 
        ORDER BY created_at DESC;
    """)
    feedbacks = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template(
        "dashboard.html",
        total_feedbacks=total_feedbacks,
        sentiment_summary=sentiment_summary,
        top_features=top_features,
        feedbacks=feedbacks
    )

# Graphical feedback endpoint
@app.route('/submit', methods=['GET'])
def submit_feedback_page():
    return render_template("submit_feedback.html", )

if __name__ == '__main__':
    # Start the scheduler in a separate thread
    scheduler_thread = threading.Thread(target=schedule_weekly_report)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    # Run the Flask app
    app.run(debug=True)
