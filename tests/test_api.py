import pytest
import json
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to the path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api import app
from src.reporting.report import generate_weekly_report


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_health_check_endpoint(client):
    """Test the health check endpoint returns 200 and correct status."""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'ok'


@patch('api.analyze_feedback_langchain')
@patch('api.spam_filter')
@patch('api.get_db_connection')
def test_create_feedback_endpoint(mock_get_db, mock_spam_filter, mock_analyze, client):
    """Test the feedback creation endpoint with valid data."""
    # Configure mocks
    mock_spam_filter.return_value = True
    mock_analyze.return_value = {
        'sentiment': 'POSITIVO',
        'feature_code': 'F001',
        'feature_reason': 'User wants more meditation content'
    }
    
    # Mock database connection and cursor
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    
    # Test data
    test_feedback = {
        'id': 'test123',
        'feedback': 'I love this app, but would like more meditation content.'
    }
    
    # Make the request
    response = client.post(
        '/feedbacks',
        data=json.dumps(test_feedback),
        content_type='application/json'
    )
    
    # Assertions
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'message' in data
    assert data['message'] == 'Feedback processed and stored successfully'
    
    # Verify mocks were called correctly
    mock_spam_filter.assert_called_once_with(test_feedback['feedback'])
    mock_analyze.assert_called_once_with(test_feedback['feedback'], test_feedback['id'])
    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()