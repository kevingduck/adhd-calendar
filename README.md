# ADHD Calendar

## Overview

ADHD Calendar is a lightweight web application designed to assist individuals with ADHD in managing their tasks and time more effectively. The app allows users to quickly input tasks, which are then automatically scheduled in their Google Calendar based on AI-estimated durations.

Key features:
- Simple web interface for task input
- Google Sign-In for easy authentication and calendar access
- AI-powered task duration estimation using Groq API
- Automatic task scheduling in Google Calendar
- Task management and viewing capabilities

## Prerequisites

Before you begin, ensure you have met the following requirements:
- Python 3.7 or higher
- pip (Python package manager)
- A Google Cloud Platform account with Calendar API enabled
- A Groq API account and API key

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/adhd-calendar.git
   cd adhd-calendar
   ```

2. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up your Google OAuth 2.0 credentials:
   - Go to the Google Cloud Console
   - Create a new project or select an existing one
   - Enable the Google Calendar API
   - Create OAuth 2.0 credentials (Web application type)
   - Download the client configuration and save it as `client_secret.json` in the project directory

4. Set up your Groq API key as an environment variable:
   ```
   export GROQ_API_KEY='your_groq_api_key_here'
   ```

5. Create and set up the SQLite database:
   ```
   sqlite3 tasks.db
   ```
   Then, in the SQLite prompt, create the tasks table:
   ```sql
   CREATE TABLE tasks (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       user_id TEXT NOT NULL,
       description TEXT NOT NULL,
       status TEXT NOT NULL,
       scheduled_time TEXT,
       estimated_duration INTEGER
   );
   ```
   Exit SQLite with `.quit`

## Configuration

1. In `app.py`, update the `redirect_uri` in the Flow configuration to match your domain:
   ```python
   flow = Flow.from_client_secrets_file(
       'client_secret.json',
       scopes=SCOPES,
       redirect_uri='https://10cob.com/oauth2callback'
   )
   ```

2. In `templates/index.html`, replace `YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com` with your actual Google Client ID.

3. Update the Nginx configuration to proxy requests to your Flask app running on port 8000.

## Usage

1. Start the Flask application:
   ```
   gunicorn --workers 3 --bind 0.0.0.0:8000 -m 007 app:app
   ```

2. Open a web browser and navigate to `https://10cob.com`

3. Sign in with your Google account and grant the necessary permissions.

4. Enter your tasks in the input field and click "Add Task".

5. The app will estimate the task duration, find a suitable time slot, and add it to your Google Calendar.

## Deployment

The application is deployed on an EC2 instance and accessible at https://10cob.com. The server is configured with Nginx as a reverse proxy to the Flask application running on port 8000.

## Contributing

Contributions to the ADHD Calendar project are welcome. Please follow these steps:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/AmazingFeature`)
3. Make your changes
4. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
5. Push to the branch (`git push origin feature/AmazingFeature`)
6. Open a Pull Request

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.

## Acknowledgements

- Google Calendar API
- Groq API for task duration estimation
- Flask web framework
- Gunicorn WSGI HTTP Server
- Nginx web server