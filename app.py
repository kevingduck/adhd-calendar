from flask import Flask, request, render_template, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from groq import Groq
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Initialize Groq client using the API key from environment variables
groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(200), nullable=False)
    estimated_time = db.Column(db.Integer, nullable=False)
    ai_response = db.Column(db.Text, nullable=True)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<Task {self.task}>'

# Create the database tables
with app.app_context():
    db.create_all()

def extract_time_estimate(response_text):
    match = re.search(r'ESTIMATE:\s*(\d+)\s*minutes', response_text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return 60  # Default to 60 minutes if no estimate found

def get_available_slots(duration_minutes, start_date=None):
    if start_date is None:
        start_date = datetime.now()
    
    end_date = start_date + timedelta(days=7)
    available_slots = []
    
    current_time = start_date.replace(hour=9, minute=0, second=0, microsecond=0)  # Start at 9 AM
    while current_time < end_date:
        if current_time.hour >= 22:  # End at 10 PM
            current_time = (current_time + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
            continue
        
        slot_end = current_time + timedelta(minutes=duration_minutes)
        
        # Check if the slot overlaps with any existing tasks
        overlapping_tasks = Task.query.filter(
            ((Task.start <= current_time) & (Task.end > current_time)) |
            ((Task.start < slot_end) & (Task.end >= slot_end)) |
            ((Task.start >= current_time) & (Task.end <= slot_end))
        ).all()
        
        if not overlapping_tasks:
            available_slots.append({
                'start': current_time.isoformat(),
                'end': slot_end.isoformat()
            })
            return available_slots  # Return the first available slot
        
        current_time += timedelta(minutes=15)  # Check every 15 minutes
    
    return available_slots

@app.route("/", methods=['GET', 'POST'])
def index():
    error = None
    follow_up_question = None

    if request.method == 'POST':
        if 'task' in request.form:
            task = request.form['task']
            session['task'] = task
            session['conversation'] = [{"role": "user", "content": task}]
        elif 'answer' in request.form:
            answer = request.form['answer']
            session['conversation'].append({"role": "user", "content": answer})
        
        # Prepare the current schedule for the AI
        current_schedule = "Current schedule:\n"
        tasks = Task.query.all()
        for task in tasks:
            current_schedule += f"{task.task}: {task.start.isoformat()} - {task.end.isoformat()}\n"
        
        # Send conversation to Groq for estimation
        prompt = """
        You are an AI assistant that estimates the time required to complete tasks and 
        suggests when to schedule them. Interactions go like this:
        1. I tell you a task 

        2. You can ask for more information in as few words as possible. No more than 8 words.
        For instance, if I say "Clean my room," you ask "Room size?" 

        DO NOT ADD ANY OTHER INFORMATION.

        3. After I provide the information, you figure out the time it will take and look at
        calendar to find a time slot and respond with a final resonse.
        
        Your final response should be formatted like this:
        "{task-name} ({est-min}): {date} {start-time} - {end-time}". 
        For example, "Clean Room (30): Mon Aug 22 2:00PM - 2:30PM".
        
        #Example interaction:
        - I say "Clean my room."
        - You say "Room size?"
        - I say "200sqft."
        - You say "Clean Room (30): Mon Aug 22 2:00PM - 2:30PM".
        """
        response = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": prompt + current_schedule
                },
                *session['conversation']
            ],
            model="mixtral-8x7b-32768",
            max_tokens=5000
        )

        ai_response = response.choices[0].message.content.strip()
        print(f'AI Response: {ai_response}')
        session['conversation'].append({"role": "assistant", "content": ai_response})

        if ai_response.startswith("ESTIMATE:"):
            # Extract the estimated time and schedule the task
            estimated_time = extract_time_estimate(ai_response)
            available_slots = get_available_slots(estimated_time)
            
            if available_slots:
                slot = available_slots[0]
                start_time = datetime.fromisoformat(slot['start'])
                end_time = datetime.fromisoformat(slot['end'])
                
                new_task = Task(
                    task=session['task'],
                    estimated_time=estimated_time,
                    ai_response=ai_response,
                    start=start_time,
                    end=end_time
                )
                db.session.add(new_task)
                db.session.commit()

                # Clear the session
                session.pop('task', None)
                session.pop('conversation', None)
            else:
                error = "No available time slots found for this task within the next week."
        else:
            # AI asked a follow-up question
            follow_up_question = ai_response

    # Prepare calendar events
    calendar_events = []
    tasks = Task.query.all()
    for task in tasks:
        calendar_events.append({
            'title': task.task,
            'start': task.start.isoformat(),
            'end': task.end.isoformat(),
            'color': '#28a745',  # green for tasks
            'extendedProps': {
                'aiResponse': task.ai_response
            }
        })

    return render_template('index.html', calendar_events=calendar_events, follow_up_question=follow_up_question, error=error)

if __name__ == "__main__":
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)