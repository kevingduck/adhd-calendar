from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import sqlite3
import requests
import os
import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app, supports_credentials=True)

# Configure Google OAuth2
SCOPES = ['https://www.googleapis.com/auth/calendar']
flow = Flow.from_client_secrets_file(
    'client_secret.json',
    scopes=SCOPES,
    redirect_uri='http://localhost:8000/oauth2callback'
)

# Groq API setup
GROQ_API_KEY = os.environ['GROQ_API_KEY']
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def get_db_connection():
    conn = sqlite3.connect('tasks.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    try:
        authorization_url, state = flow.authorization_url()
        session['state'] = state
        return jsonify({'auth_url': authorization_url})
    except Exception as e:
        print(f"Error in login route: {str(e)}")
        return jsonify({'error': 'Failed to initialize login flow'}), 500
    
@app.route('/oauth2callback')
def oauth2callback():
    try:
        flow.fetch_token(authorization_response=request.url)
        credentials = flow.credentials
        session['credentials'] = credentials_to_dict(credentials)
        return '<script>window.close();</script>'
    except Exception as e:
        print(f"Error in oauth2callback: {str(e)}")
        return f'<script>alert("Authentication failed: {str(e)}"); window.close();</script>'

@app.route('/check_auth')
def check_auth():
    if 'credentials' in session:
        return jsonify({'authenticated': True})
    return jsonify({'authenticated': False})

@app.route('/add_task', methods=['POST'])
def add_task():
    if 'credentials' not in session:
        return jsonify({'error': 'User not authenticated'}), 401
    
    task_description = request.json['task']
    
    estimated_time = estimate_task_time(task_description)
    suitable_slot = find_free_time_slot(estimated_time)
    
    if suitable_slot:
        add_event_to_calendar(task_description, suitable_slot, estimated_time)
        save_task_to_db(session['credentials']['client_id'], task_description, 'Scheduled', suitable_slot, estimated_time)
        return jsonify({
            'message': 'Task scheduled successfully',
            'time': suitable_slot.isoformat(),
            'duration': estimated_time
        })
    else:
        save_task_to_db(session['credentials']['client_id'], task_description, 'Unscheduled', None, estimated_time)
        return jsonify({'error': 'Could not find a suitable time slot'}), 400

def estimate_task_time(task_description):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "mixtral-8x7b-32768",
        "messages": [
            {"role": "system", "content": "You are an AI assistant that estimates the time required to complete tasks. Provide your estimate in minutes."},
            {"role": "user", "content": f"Estimate the time in minutes to complete this task: {task_description}"}
        ],
        "max_tokens": 100
    }
    
    response = requests.post(GROQ_API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        estimate = response.json()['choices'][0]['message']['content']
        try:
            return int(estimate.split()[0])  # Assume the first word is the number of minutes
        except ValueError:
            return 60  # Default to 1 hour if parsing fails
    else:
        print(f"Error from Groq API: {response.text}")
        return 60  # Default to 1 hour if API call fails

def find_free_time_slot(duration):
    credentials = Credentials(**session['credentials'])
    service = build('calendar', 'v3', credentials=credentials)
    
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                          maxResults=10, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])
    
    if not events:
        return datetime.datetime.now() + datetime.timedelta(hours=1)
    
    last_event_end = datetime.datetime.fromisoformat(events[-1]['end'].get('dateTime', events[-1]['end'].get('date')))
    return last_event_end + datetime.timedelta(minutes=15)

def add_event_to_calendar(task, start_time, duration):
    credentials = Credentials(**session['credentials'])
    service = build('calendar', 'v3', credentials=credentials)
    
    event = {
        'summary': task,
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': 'America/New_York',
        },
        'end': {
            'dateTime': (start_time + datetime.timedelta(minutes=duration)).isoformat(),
            'timeZone': 'America/New_York',
        },
    }
    service.events().insert(calendarId='primary', body=event).execute()

def save_task_to_db(user_id, description, status, scheduled_time, estimated_duration):
    conn = get_db_connection()
    conn.execute('INSERT INTO tasks (user_id, description, status, scheduled_time, estimated_duration) VALUES (?, ?, ?, ?, ?)',
                 (user_id, description, status, scheduled_time, estimated_duration))
    conn.commit()
    conn.close()

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)