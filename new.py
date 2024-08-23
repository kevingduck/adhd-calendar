from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from groq import Groq
import csv
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize Groq client using the API key from environment variables
groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))

# Simulated calendar (replace with actual Google Calendar integration later)
calendar = []

@app.route("/sms", methods=['POST'])
def sms_reply():
    # Get the message body from the incoming SMS
    task = request.form['Body']

    # Send task to Groq for estimation
    response = groq_client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are an AI assistant that estimates the time required to complete tasks. Provide your estimate in minutes."
            },
            {
                "role": "user",
                "content": f"Estimate the time required to complete this task: {task}"
            }
        ],
        model="mixtral-8x7b-32768",
        max_tokens=100
    )

    # Extract the estimated time from the Groq response
    estimated_time = int(response.choices[0].message.content.strip())

    # Schedule the task (for now, just add it to our simulated calendar)
    now = datetime.now()
    task_end_time = now + timedelta(minutes=estimated_time)
    calendar.append({
        'task': task,
        'estimated_time': estimated_time,
        'scheduled_start': now.isoformat(),
        'scheduled_end': task_end_time.isoformat()
    })

    # Save to CSV
    with open('tasks.csv', 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['task', 'estimated_time', 'scheduled_start', 'scheduled_end'])
        if csvfile.tell() == 0:
            writer.writeheader()
        writer.writerow(calendar[-1])

    # Prepare response to send back via SMS
    resp = MessagingResponse()
    resp.message(f"Task '{task}' scheduled for {estimated_time} minutes, starting now.")

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)