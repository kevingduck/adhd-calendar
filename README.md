# ADHD Calendar

ADHD Calendar is a Flask-based web application designed to help individuals with ADHD manage their tasks and schedule more effectively. It uses AI to estimate task durations and automatically schedules tasks in available time slots.

## Features

- AI-powered task duration estimation
- Automatic task scheduling based on available time slots
- Interactive calendar interface
- Randomly generated events to simulate a realistic schedule
- Persistence of tasks using SQLite database

## Technologies Used

- Flask: Web framework
- SQLAlchemy: ORM for database management
- Groq: AI model for task estimation
- FullCalendar: JavaScript calendar library
- SQLite: Database for storing tasks

## Prerequisites

Before you begin, ensure you have met the following requirements:

- Python 3.7+
- pip (Python package manager)
- A Groq API key

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/adhd-calendar.git
   cd adhd-calendar
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root and add your Groq API key:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```

## Usage

1. Start the Flask application:
   ```
   python app.py
   ```

2. Open a web browser and navigate to `http://localhost:8080`

3. You'll see a calendar populated with random events for the current week.

4. To add a new task:
   - Enter the task description in the input field and click "Add Task"
   - If the AI needs more information, it will ask a follow-up question
   - Once the AI has enough information, it will estimate the task duration and schedule it in an available time slot

5. View your scheduled tasks on the calendar

## Contributing

Contributions to the ADHD Calendar project are welcome. Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Flask](https://flask.palletsprojects.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Groq](https://groq.com/)
- [FullCalendar](https://fullcalendar.io/)