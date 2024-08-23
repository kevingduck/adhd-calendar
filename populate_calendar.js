require('dotenv').config();
const { Pool } = require('pg');

const pool = new Pool({
  user: process.env.DB_USER,
  host: process.env.DB_HOST,
  database: process.env.DB_NAME,
  password: process.env.DB_PASSWORD,
  port: process.env.DB_PORT,
});

const tasks = [
  "Team meeting",
  "Project review",
  "Client call",
  "Lunch break",
  "Code review",
  "Email catchup",
  "Planning session",
  "Training workshop"
];

function randomTask() {
  return tasks[Math.floor(Math.random() * tasks.length)];
}

function randomDuration() {
  return [15, 30, 60][Math.floor(Math.random() * 3)];
}

async function checkTableStructure() {
  const client = await pool.connect();
  try {
    const res = await client.query(`
      SELECT column_name, data_type 
      FROM information_schema.columns 
      WHERE table_name = 'calendar_items'
    `);
    console.log('Current table structure:', res.rows);
  } finally {
    client.release();
  }
}

async function addEndTimeColumn() {
    const client = await pool.connect();
    try {
      const checkColumn = await client.query(`
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'calendar_items' AND column_name = 'end_time'
      `);
      
      if (checkColumn.rows.length === 0) {
        console.log('end_time column does not exist. Please add it manually using a database administration tool.');
        process.exit(1);
      } else {
        console.log('end_time column already exists');
      }
    } catch (error) {
      console.error('Error checking end_time column:', error);
      process.exit(1);
    } finally {
      client.release();
    }
  }

async function populateCalendar() {
  try {
    const currentDate = new Date();
    const startDate = new Date(currentDate.getFullYear(), currentDate.getMonth(), currentDate.getDate());
  
    for (let i = 0; i < 5; i++) { // Monday to Friday
      let currentDateTime = new Date(startDate);
      currentDateTime.setDate(currentDateTime.getDate() + i);
      currentDateTime.setHours(8, 0, 0, 0); // Start at 8:00 AM

      while (currentDateTime.getHours() < 18) { // Until 6:00 PM
        const task = randomTask();
        const duration = randomDuration();
        const endDateTime = new Date(currentDateTime.getTime() + duration * 60000);

        await pool.query(
          'INSERT INTO calendar_items(task, estimated_time, start_time, end_time) VALUES($1, $2, $3, $4)',
          [task, `${duration} minutes`, currentDateTime.toISOString(), endDateTime.toISOString()]
        );

        currentDateTime = endDateTime;
        if (currentDateTime.getMinutes() === 30) {
          currentDateTime.setMinutes(0);
          currentDateTime.setHours(currentDateTime.getHours() + 1);
        } else {
          currentDateTime.setMinutes(30);
        }
      }
    }

    console.log('Calendar populated successfully');
  } catch (error) {
    console.error('Error populating calendar:', error);
  }
}

async function main() {
  try {
    await checkTableStructure();
    await addEndTimeColumn();
    await populateCalendar();
  } catch (error) {
    console.error('Error in main function:', error);
  } finally {
    await pool.end();
  }
}

main();