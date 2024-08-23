document.addEventListener('DOMContentLoaded', () => {
    const taskInput = document.getElementById('task-description');
    const submitButton = document.getElementById('submit-task');
    const aiInteraction = document.getElementById('ai-interaction');
    const taskList = document.getElementById('task-list');
    const calendar = document.getElementById('calendar');

    loadCalendar();

    submitButton.addEventListener('click', () => {
        const task = taskInput.value;
        if (task) {
            sendTaskToAI(task);
        }
    });

    async function sendTaskToAI(task) {
        try {
            const response = await fetch('/api/tasks', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ task })
            });
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            const data = await response.json();
            displayAIPrompt(data.prompt, task);
            // Store the original task and AI's question for later use
            window.originalTask = task;
            window.aiQuestion = data.prompt;
        } catch (error) {
            console.error('Error sending task to AI:', error);
            aiInteraction.innerHTML = `<p>Error: ${error.message}</p>`;
        }
    }

    async function getTaskEstimate(userResponse) {
        try {
            const response = await fetch('/api/tasks/estimate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    task: window.originalTask,
                    userResponse: userResponse,
                    aiQuestion: window.aiQuestion
                })
            });
            if (!response.ok) {
                const errorData = await response.json();
                console.error('Server error:', errorData);
                throw new Error(errorData.error || 'Unknown error occurred');
            }
            const data = await response.json();
            displayTaskSuggestion(window.originalTask, data.estimatedTime, data.suggestedSlot);
        } catch (error) {
            console.error('Error getting task estimate:', error);
            aiInteraction.innerHTML += `<p>Error: ${error.message}</p>`;
        }
    }

    function displayAIPrompt(prompt, task) {
        aiInteraction.innerHTML = `
            <p>AI: ${prompt}</p>
            <input type="text" id="ai-response" placeholder="Your response">
            <button id="respond-to-ai">Respond</button>
        `;

        document.getElementById('respond-to-ai').addEventListener('click', () => {
            const userResponse = document.getElementById('ai-response').value;
            getTaskEstimate(task, userResponse);
        });
    }

    async function getTaskEstimate(task, userResponse) {
        try {
            const response = await fetch('/api/tasks/estimate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ task, userResponse })
            });
            if (!response.ok) {
                const errorData = await response.json();
                console.error('Server error:', errorData);
                throw new Error(errorData.error || 'Unknown error occurred');
            }
            const data = await response.json();
            displayTaskSuggestion(task, data.estimatedTime, data.suggestedSlot);
        } catch (error) {
            console.error('Error getting task estimate:', error);
            // Display error to user
            aiInteraction.innerHTML += `<p>Error: ${error.message}</p>`;
        }
    }

    function displayTaskSuggestion(task, estimatedTime, suggestedSlot) {
        const taskElement = document.createElement('div');
        taskElement.classList.add('task-item');
        taskElement.innerHTML = `
            <h3>${task}</h3>
            <p>Estimated time: ${estimatedTime}</p>
            <p>Suggested slot: ${suggestedSlot}</p>
            <button class="add-task">Add</button>
            <button class="edit-task">Edit</button>
        `;

        taskList.appendChild(taskElement);

        taskElement.querySelector('.add-task').addEventListener('click', () => addTaskToCalendar(task, estimatedTime, suggestedSlot));
        taskElement.querySelector('.edit-task').addEventListener('click', () => editTask(taskElement, task, estimatedTime, suggestedSlot));
    }

    async function addTaskToCalendar(task, estimatedTime, scheduledTime) {
        try {
            const response = await fetch('/api/calendar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ task, estimatedTime, scheduledTime })
            });
            if (response.ok) {
                loadCalendar();
            }
        } catch (error) {
            console.error('Error adding task to calendar:', error);
        }
    }

    function editTask(taskElement, task, estimatedTime, suggestedSlot) {
        taskElement.innerHTML = `
            <input type="text" value="${task}" id="edit-task-description">
            <input type="text" value="${estimatedTime}" id="edit-estimated-time">
            <input type="datetime-local" value="${suggestedSlot}" id="edit-scheduled-time">
            <button class="save-edit">Save</button>
        `;

        taskElement.querySelector('.save-edit').addEventListener('click', async () => {
            const updatedTask = document.getElementById('edit-task-description').value;
            const updatedEstimatedTime = document.getElementById('edit-estimated-time').value;
            const updatedScheduledTime = document.getElementById('edit-scheduled-time').value;

            try {
                const response = await fetch(`/api/tasks/${taskElement.dataset.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        task: updatedTask,
                        estimatedTime: updatedEstimatedTime,
                        scheduledTime: updatedScheduledTime
                    })
                });
                if (response.ok) {
                    loadCalendar();
                    displayTaskSuggestion(updatedTask, updatedEstimatedTime, updatedScheduledTime);
                }
            } catch (error) {
                console.error('Error updating task:', error);
            }
        });
    }

    async function loadCalendar() {
        try {
            const response = await fetch('/api/calendar');
            const calendarItems = await response.json();
            displayCalendar(calendarItems);
        } catch (error) {
            console.error('Error loading calendar:', error);
        }
    }

    function displayCalendar(calendarItems) {
        calendar.innerHTML = '<h2>Calendar</h2>';
        calendarItems.forEach(item => {
            const itemElement = document.createElement('div');
            itemElement.classList.add('calendar-item');
            itemElement.innerHTML = `
                <h3>${item.task}</h3>
                <p>Time: ${new Date(item.start_time).toLocaleString()}</p>
                <p>Estimated duration: ${item.estimated_time}</p>
            `;
            calendar.appendChild(itemElement);
        });
    }
});