from flask import Flask, request, render_template, redirect, url_for, session, jsonify
from groq import Groq
import csv
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management

# Initialize Groq client using the API key from environment variables
groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))

# Dummy calendar with some existing entries
dummy_calendar = [
    {"task": "Team Meeting", "start": "2024-08-22T09:00:00", "end": "2024-08-22T10:00:00"},
    {"task": "Lunch Break", "start": "2024-08-22T12:00:00", "end": "2024-08-22T13:00:00"},
    {"task": "Project Deadline", "start": "2024-08-22T16:00:00", "end": "2024-08-22T17:00:00"},
    {"task": "Gym", "start": "2024-08-22T18:00:00", "end": "2024-08-22T19:30:00"},
]

# Simulated calendar for new tasks
calendar = []

def extract_time_estimate(response_text):
    match = re.search(r'ESTIMATE:\s*(\d+)\s*minutes', response_text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return 60  # Default to 60 minutes if no estimate found

def get_available_slots(duration_minutes):
    available_slots = []
    now = datetime.now()
    end_of_day = now.replace(hour=22, minute=0, second=0, microsecond=0)
    
    current_time = now
    while current_time < end_of_day:
        slot_end = current_time + timedelta(minutes=duration_minutes)
        if slot_end > end_of_day:
            break
        
        is_available = True
        for event in dummy_calendar + calendar:
            event_start = datetime.fromisoformat(event['start'])
            event_end = datetime.fromisoformat(event['end'])
            if (current_time < event_end and slot_end > event_start):
                is_available = False
                current_time = event_end
                break
        
        if is_available:
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
        for event in dummy_calendar + calendar:
            current_schedule += f"{event['task']}: {event['start']} - {event['end']}\n"
        
        # Send conversation to Groq for estimation
        prompt = """
        You are an AI assistant that estimates the time required to complete tasks and 
        suggests when to schedule them. Interactions go like this:
        1. I tell you a task 

        2. You can ask for more information in as few words as possible. No more than 10 words.
        For instance, if I say "Clean my room," you ask "Room size?"

        3. After I provide the information, you estimate the time it will take and look at
        calendar to find a time slot.
        
        Your final response should be formatted like this:
        "{task-name} ({est-min}): {date} {start-time} - {end-time}". 
        For example, "Clean Room (30): Mon Aug 22 2:00PM - 2:30PM".
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
                
                calendar.append({
                    'task': session['task'],
                    'estimated_time': estimated_time,
                    'ai_response': ai_response,
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat()
                })

                # Save to CSV
                with open('tasks.csv', 'a', newline='') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=['task', 'estimated_time', 'ai_response', 'start', 'end'])
                    if csvfile.tell() == 0:
                        writer.writeheader()
                    writer.writerow(calendar[-1])

                # Clear the session
                session.pop('task', None)
                session.pop('conversation', None)
            else:
                error = "No available time slots found for this task."
        else:
            # AI asked a follow-up question
            follow_up_question = ai_response

    # Prepare calendar events
    calendar_events = []
    for event in dummy_calendar:
        calendar_events.append({
            'title': event['task'],
            'start': event['start'],
            'end': event['end'],
            'color': '#3788d8'  # blue for dummy events
        })
    for task in calendar:
        calendar_events.append({
            'title': task['task'],
            'start': task['start'],
            'end': task['end'],
            'color': '#28a745',  # green for new tasks
            'extendedProps': {
                'aiResponse': task['ai_response']
            }
        })

    return render_template('index.html', calendar_events=calendar_events, follow_up_question=follow_up_question, error=error)

if __name__ == "__main__":
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)