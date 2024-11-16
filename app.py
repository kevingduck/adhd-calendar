from flask import Flask, render_template, request, jsonify
from anthropic import Anthropic
import json
import datetime
import sqlite3
import os
from dotenv import load_dotenv

app = Flask(__name__)

# Load environment variables
load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Initialize the Anthropic client
anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        start DATETIME NOT NULL,
                        end DATETIME NOT NULL,
                        steps TEXT NOT NULL,
                        hours REAL NOT NULL
                    )''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks ORDER BY start DESC")
    tasks = cursor.fetchall()
    conn.close()

    # Convert tasks to a list of dictionaries
    task_list = [{
        'id': task[0],
        'title': task[1],
        'start': task[2],
        'end': task[3],
        'steps': json.loads(task[4]),
        'hours': task[5]
    } for task in tasks]

    return render_template('index.html', tasks=task_list)

@app.route('/get_estimate', methods=['POST'])
def get_estimate():
    data = request.json
    task = data.get('task')
    
    if not task:
        return jsonify({'error': 'No task provided'}), 400
    
    try:
        message = anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=500,
            temperature=0,
            messages=[{
                "role": "user",
                "content": f"""For the task: "{task}"
Please analyze this task and provide:
1. How many hours it will likely take (be realistic)
2. Three specific steps to get started

Format your response as valid JSON with this exact structure:
{{
    "hours": number,
    "steps": [string, string, string]
}}
Just the JSON, no other text."""
            }]
        )
        
        # Extract the response content
        response_text = message.content[0].text.strip()
        estimate = json.loads(response_text)
        
        # Validate the response structure
        if not isinstance(estimate.get('hours'), (int, float)):
            raise ValueError('Invalid hours value')
        if not isinstance(estimate.get('steps'), list):
            raise ValueError('Invalid steps format')
            
        # Constrain hours to reasonable values
        estimate['hours'] = max(0.5, min(8, float(estimate['hours'])))
        
        return jsonify(estimate)
        
    except Exception as e:
        print(f"Error getting Claude estimate: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/add_task', methods=['POST'])
def add_task():
    data = request.json
    task = data.get('task')
    duration = data.get('duration')
    date = data.get('date')
    time = data.get('time')
    steps = data.get('steps')
    
    if not task or not duration or not date or not time:
        return jsonify({'error': 'Missing task details'}), 400
    
    try:
        start_time = datetime.datetime.strptime(f"{date} {time}", '%Y-%m-%d %H:%M')
        end_time = start_time + datetime.timedelta(hours=float(duration))
        
        # Save to database
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tasks (title, start, end, steps, hours) VALUES (?, ?, ?, ?, ?)",
            (task, start_time, end_time, json.dumps(steps), float(duration))
        )
        conn.commit()
        conn.close()
        
        return jsonify({
            'title': task,
            'start': start_time.isoformat(),
            'end': end_time.isoformat(),
            'steps': steps,
            'hours': duration
        })
        
    except ValueError as e:
        return jsonify({'error': 'Invalid date or time format'}), 400
    except Exception as e:
        print(f"Error adding task: {e}")
        return jsonify({'error': str(e)}), 500
    
@app.route('/update_task/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.json
    task = data.get('task')
    duration = data.get('duration')
    date = data.get('date')
    time = data.get('time')
    steps = data.get('steps')
    
    if not all([task, duration, date, time, steps]):
        return jsonify({'error': 'Missing task details'}), 400
    
    try:
        start_time = datetime.datetime.strptime(f"{date} {time}", '%Y-%m-%d %H:%M')
        end_time = start_time + datetime.timedelta(hours=float(duration))
        
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE tasks 
            SET title = ?, start = ?, end = ?, steps = ?, hours = ?
            WHERE id = ?
        """, (task, start_time, end_time, json.dumps(steps), float(duration), task_id))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error updating task: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/delete_task/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    try:
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error deleting task: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

