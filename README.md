# Task Scheduler with AI Assistant

## Overview

This project is a task scheduling application that uses an AI assistant to help estimate task durations and suggest scheduling times. It's designed to help users manage their time more effectively by leveraging AI insights.

**Note: This project is currently a work in progress and may have limitations or bugs.**

## Features

- Input tasks and get AI-assisted time estimates
- AI-suggested scheduling based on your existing calendar
- Simple calendar view of scheduled tasks

## Prerequisites

- Node.js (v14 or later recommended)
- PostgreSQL database
- Groq API key

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/task-scheduler-ai.git
   cd task-scheduler-ai
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Set up your environment variables:
   Create a `.env` file in the root directory with the following contents:
   ```
   DB_USER=your_database_user
   DB_HOST=your_database_host
   DB_NAME=your_database_name
   DB_PASSWORD=your_database_password
   DB_PORT=your_database_port
   GROQ_API_KEY=your_groq_api_key
   ```

4. Set up your PostgreSQL database:
   - Create a new database
   - Create a `calendar_items` table (schema to be provided)

5. Start the server:
   ```
   node app.js
   ```

6. Open a web browser and navigate to `http://localhost:3000`

## Current Limitations

- The AI responses may sometimes be inconsistent
- Error handling is basic and may not cover all edge cases
- The UI is minimal and may lack some user-friendly features
- Calendar functionality is limited

## Contributing

As this is a work in progress, contributions are welcome! Please feel free to submit issues or pull requests.

## License

[MIT License](https://opensource.org/licenses/MIT)