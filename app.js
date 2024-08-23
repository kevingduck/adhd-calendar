require('dotenv').config();
const express = require('express');
const bodyParser = require('body-parser');
const { Pool } = require('pg');
const axios = require('axios');

const app = express();
const port = 3000;

const pool = new Pool({
    user: process.env.DB_USER,
    host: process.env.DB_HOST,
    database: process.env.DB_NAME,
    password: process.env.DB_PASSWORD,
    port: process.env.DB_PORT,
});

pool.query('SELECT NOW()', (err, res) => {
    if (err) {
        console.error('Error connecting to the database', err);
    } else {
        console.log('Successfully connected to the database');
    }
});

const GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions';

app.use(bodyParser.json());
app.use(express.static('public'));

async function interactWithGroq(messages) {
    try {
        const response = await axios.post(GROQ_API_URL, {
            model: 'mixtral-8x7b-32768',
            messages: messages,
            max_tokens: 150
        }, {
            headers: {
                'Authorization': `Bearer ${process.env.GROQ_API_KEY}`,
                'Content-Type': 'application/json'
            }
        });
        return response.data.choices[0].message.content;
    } catch (error) {
        console.error('Error interacting with Groq:', error);
        throw error;
    }
}

app.post('/api/tasks', async (req, res) => {
    const { task } = req.body;
    const prompt = `
        You are an AI assistant that estimates the time required to complete tasks and 
        suggests when to schedule them. Interactions go like this:
        1. I tell you a task 

        2. You can ask for more information in as few words as possible. No more than 5 words.
        For instance, if I say "Clean my room," you ask "Room size?"

        DO NOT ADD ANY OTHER INFORMATION IN THIS STEP. JUST ASK FOR MORE INFORMATION.

        3. After I provide the information, you estimate the time it will take and look at
        calendar to find a time slot.
        
        Your final response should be formatted like this:
        "ESTIMATE: {est-min} minutes - {task-name}". 
        For example, "ESTIMATE: 30 minutes - Clean Room".

        DO NOT ADD ANY OTHER INFORMATION IN THIS STEP. JUST PROVIDE THE REQUESTED INFORMATION 
        IN THE REQUESTED FORMAT.
        `
    try {
        const initialPrompt = await interactWithGroq([
            { role: 'system', content: prompt },
            { role: 'user', content: `Task: ${task}` }
        ]);
        res.json({ prompt: initialPrompt.trim() });
    } catch (error) {
        console.error('Error processing task:', error);
        res.status(500).json({ error: 'Error processing task' });
    }
});

app.post('/api/tasks/estimate', async (req, res) => {
    const { task, userResponse, aiQuestion } = req.body;
    try {
        const calendarItems = await pool.query('SELECT * FROM calendar_items');
        console.log('Calendar items:', calendarItems.rows);
        const aiResponse = await interactWithGroq([
            { role: 'system', content: 'You are a helpful AI assistant. Estimate the time for the task and suggest a specific time slot based on the existing calendar. Respond ONLY with two lines: "Time: [estimated time]" and "Date: [suggested date and time]". Do not provide any explanations.' },
            { role: 'user', content: `Original task: ${task}\nAI question: ${aiQuestion}\nUser response: ${userResponse}\nExisting calendar: ${JSON.stringify(calendarItems.rows)}` }
        ]);
        console.log('AI response:', aiResponse);
        
        // Extract information from the AI response
        const timeMatch = aiResponse.match(/Time:\s*(.*)/i);
        const dateMatch = aiResponse.match(/Date:\s*(.*)/i);
        
        const parsedResponse = {
            estimatedTime: timeMatch ? timeMatch[1].trim() : '30 minutes',
            suggestedSlot: dateMatch ? dateMatch[1].trim() : 'Next available slot'
        };
        
        res.json(parsedResponse);
    } catch (error) {
        console.error('Error in /api/tasks/estimate:', error);
        res.status(500).json({ 
            error: 'Error estimating task', 
            details: error.message,
            estimatedTime: '30 minutes',
            suggestedSlot: 'Next available slot'
        });
    }
});

app.get('/api/calendar', async (req, res) => {
    try {
        const result = await pool.query('SELECT * FROM calendar_items ORDER BY start_time');
        res.json(result.rows);
    } catch (error) {
        res.status(500).json({ error: 'Error fetching calendar items' });
    }
});

app.post('/api/calendar', async (req, res) => {
    const { task, estimatedTime, scheduledTime } = req.body;
    try {
        const result = await pool.query(
            'INSERT INTO calendar_items(task, estimated_time, start_time) VALUES($1, $2, $3) RETURNING *',
            [task, estimatedTime, scheduledTime]
        );
        res.json(result.rows[0]);
    } catch (error) {
        res.status(500).json({ error: 'Error adding task to calendar' });
    }
});

app.put('/api/tasks/:id', async (req, res) => {
    const { id } = req.params;
    const { task, estimatedTime, scheduledTime } = req.body;
    try {
        const result = await pool.query(
            'UPDATE calendar_items SET task = $1, estimated_time = $2, start_time = $3 WHERE id = $4 RETURNING *',
            [task, estimatedTime, scheduledTime, id]
        );
        res.json(result.rows[0]);
    } catch (error) {
        res.status(500).json({ error: 'Error updating task' });
    }
});

app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
});