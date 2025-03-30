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
            feedback_data['sentiment'] = analysis_result['sentiment']
            feedback_data['feature_code'] = analysis_result.get('feature_code')
            feedback_data['feature_reason'] = analysis_result.get('feature_reason')
            
            # Insert feedback into the database
            insert_feedback(feedback_data)
            return jsonify(analysis_result), 201
        else:
            return jsonify({'error': 'Feedback is spam'}), 400
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
    total_feedbacks = get_total_feedback_count()
    sentiment_data = get_sentiment_data()
    top_features = get_top_requested_features()
    feedbacks = get_detailed_feedbacks()
    
    sentiment_summary = [
        {
            'sentiment': row['sentiment'],
            'count': row['count'],
            'percentage': row['percentage']
        } for row in sentiment_data
    ]
    
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
