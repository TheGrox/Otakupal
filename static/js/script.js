// static/js/script.js (Updated)
const chatWindow = document.getElementById('chatWindow');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const sidebar = document.getElementById('sidebar');
const hamburgerButton = document.getElementById('hamburgerButton');
const newChatButton = document.getElementById('newChatButton');
const chatHistoryList = document.getElementById('chatHistoryList');
const chatSearch = document.getElementById('chatSearch');

let currentChatId = null; // To store the ID of the currently active chat

// Focus input on load
messageInput.focus();

// Initial load of chat history and current chat
document.addEventListener('DOMContentLoaded', () => {
    currentChatId = chatWindow.dataset.currentChatId; // Get initial chat ID from HTML
    loadChatHistory();
    // If there are messages already rendered (e.g., on page refresh), scroll to bottom
    chatWindow.scrollTop = chatWindow.scrollHeight;
});

// Toggle sidebar
hamburgerButton.addEventListener('click', () => {
    sidebar.classList.toggle('open');
});

// New Chat button handler
newChatButton.addEventListener('click', async () => {
    // No confirmation needed if it's already a new, empty chat
    if (chatWindow.children.length > 0 && !confirm("Start a new chat? Your current conversation will be saved.")) {
        return;
    }
    try {
        const response = await fetch('/new_chat', { method: 'POST' });
        const data = await response.json();
        if (data.success) {
            currentChatId = data.new_chat_id;
            clearChatWindow();
            loadChatHistory(); // Refresh history to show new chat
            updateActiveChatInSidebar(currentChatId);
            messageInput.focus();
            sidebar.classList.remove('open'); // Close sidebar after new chat
        } else {
            alert("Failed to start a new chat.");
        }
    } catch (error) {
        console.error('Error starting new chat:', error);
        alert("Error starting new chat. Please try again.");
    }
});

// Send message when Enter is pressed
function handleKeyDown(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
}

// Send message function
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;

    addMessage(message, 'user');
    messageInput.value = '';
    messageInput.style.height = 'auto';

    showTypingIndicator();

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });

        const data = await response.json();
        removeTypingIndicator();
        addMessage(data.response, 'bot');

        // Update currentChatId if it was a new chat and title was generated
        if (data.current_chat_id && data.current_chat_id !== currentChatId) {
            currentChatId = data.current_chat_id;
            updateActiveChatInSidebar(currentChatId); // Update active class immediately
        }

        // Refresh history if the backend indicates a title change (first message)
        if (data.refresh_history) {
            loadChatHistory();
        }

    } catch (error) {
        removeTypingIndicator();
        addMessage("Sorry, I'm having trouble connecting. Please try again later.", 'bot');
        console.error('Error:', error);
    }
}

// Add message to chat
function addMessage(content, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    messageDiv.dataset.sessionId = currentChatId; // Add session ID here

    const avatar = document.createElement('div');
    avatar.className = 'avatar';

    if (sender === 'user') {
        avatar.innerHTML = '<i class="fas fa-user"></i>';
    } else {
        avatar.innerHTML = '<i class="fas fa-robot"></i>';
    }

    const contentDiv = document.createElement('div');
    contentDiv.className = 'content';

    // Simple markdown to HTML conversion
    let htmlContent = content
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/_(.*?)_/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>');

    // Convert newlines to <br>
    htmlContent = htmlContent.replace(/\n/g, '<br>');
    contentDiv.innerHTML = htmlContent;

    // Create action buttons
    const actionDiv = document.createElement('div');
    actionDiv.className = 'action-buttons';

    if (sender === 'user') {
        actionDiv.innerHTML = `
            <button class="edit-button" onclick="editMessage(this)"><i class="fas fa-pen"></i></button>
            <button class="delete-button" onclick="deleteMessage(this)"><i class="fas fa-trash-alt"></i></button>
        `;
    } else {
        actionDiv.innerHTML = `
            <button class="edit-button" onclick="editMessage(this)"><i class="fas fa-pen"></i></button>
            <button class="delete-button" onclick="deleteMessage(this)"><i class="fas fa-trash-alt"></i></button>
            <button class="regenerate-button" onclick="regenerateResponse(this)"><i class="fas fa-redo"></i></button>
        `;
    }

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(actionDiv);
    chatWindow.appendChild(messageDiv);

    // Scroll to bottom
    chatWindow.scrollTop = chatWindow.scrollHeight;
}


// Clear all messages from the chat window
function clearChatWindow() {
    chatWindow.innerHTML = '';
}

// Show typing indicator
function showTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot-message';
    typingDiv.id = 'typingIndicator';

    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.innerHTML = '<i class="fas fa-robot"></i>';

    const content = document.createElement('div');
    content.className = 'content typing-indicator';
    content.innerHTML = `
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
    `;

    typingDiv.appendChild(avatar);
    typingDiv.appendChild(content);
    chatWindow.appendChild(typingDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

// Remove typing indicator
function removeTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.remove();
    }
}

// Load chat history into the sidebar
async function loadChatHistory() {
    try {
        const response = await fetch('/get_chat_sessions'); // Call the new endpoint
        const data = await response.json();
        chatHistoryList.innerHTML = ''; // Clear existing history

        if (data.sessions && data.sessions.length > 0) {
            data.sessions.forEach(session => {
                const item = document.createElement('div');
                item.className = 'chat-history-item';
                item.dataset.sessionId = session.id;
                if (session.id == currentChatId) {
                    item.classList.add('active');
                }

                const titleSpan = document.createElement('span');
                // Use the title if available, otherwise format the creation timestamp
                titleSpan.textContent = session.title || formatTimestamp(session.created_at);
                item.appendChild(titleSpan);

                const deleteButton = document.createElement('button');
                deleteButton.className = 'delete-chat-button';
                deleteButton.innerHTML = '<i class="fas fa-trash-alt"></i>';
                deleteButton.title = 'Delete Chat';
                deleteButton.addEventListener('click', (e) => {
                    e.stopPropagation(); // Prevent loading chat when deleting
                    deleteChat(session.id, session.title || formatTimestamp(session.created_at));
                });
                item.appendChild(deleteButton);

                item.addEventListener('click', () => loadSpecificChat(session.id));
                chatHistoryList.appendChild(item);
            });
        } else {
            chatHistoryList.innerHTML = '<p style="padding: 10px 20px; color: #888;">No past chats.</p>';
        }
    } catch (error) {
        console.error('Error loading chat history:', error);
    }
}

// Load a specific chat into the main window
async function loadSpecificChat(sessionId) {
    if (sessionId == currentChatId) { // Use == for type coercion if IDs might be string/number
        sidebar.classList.remove('open'); // Just close sidebar if already active
        return;
    }

    try {
        const response = await fetch(`/load_chat/${sessionId}`);
        const data = await response.json();
        if (data.success) {
            currentChatId = data.current_chat_id;
            clearChatWindow();
            data.messages.forEach(msg => addMessage(msg.content, msg.sender));
            updateActiveChatInSidebar(currentChatId);
            messageInput.focus();
            sidebar.classList.remove('open'); // Close sidebar after loading chat
        } else {
            alert("Failed to load chat.");
        }
    } catch (error) {
        console.error('Error loading specific chat:', error);
        alert("Error loading chat. Please try again.");
    }
}

// Delete a chat session
async function deleteChat(sessionId, chatTitle) {
    if (!confirm(`Are you sure you want to delete "${chatTitle}"? This action cannot be undone.`)) {
        return;
    }

    try {
        const response = await fetch(`/delete_chat/${sessionId}`, { method: 'DELETE' });
        const data = await response.json();
        if (data.success) {
            alert(`Chat "${chatTitle}" deleted successfully.`);
            currentChatId = data.new_current_chat_id; // Update current chat ID from backend response
            clearChatWindow(); // Clear current view
            // If the new current chat is different (i.e., a new one was created), load its messages
            if (currentChatId) { // Check if currentChatId is not null/undefined
                const newChatMessagesResponse = await fetch(`/load_chat/${currentChatId}`);
                const newChatMessagesData = await newChatMessagesResponse.json();
                if (newChatMessagesData.success) {
                    newChatMessagesData.messages.forEach(msg => addMessage(msg.content, msg.sender));
                }
            }
            loadChatHistory(); // Reload history to reflect deletion and new active chat
            updateActiveChatInSidebar(currentChatId); // Set new active chat
            messageInput.focus();
        } else {
            alert("Failed to delete chat.");
        }
    } catch (error) {
        console.error('Error deleting chat:', error);
        alert("Error deleting chat. Please try again.");
    }
}

// Update active class in sidebar
function updateActiveChatInSidebar(activeId) {
    document.querySelectorAll('.chat-history-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.sessionId == activeId) { // Use == for type coercion
            item.classList.add('active');
        }
    });
}

// Helper to format timestamp for display
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Event listeners
sendButton.addEventListener('click', sendMessage);
messageInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// Search chat history
chatSearch.addEventListener('input', () => {
    const searchTerm = chatSearch.value.toLowerCase();
    const chatHistoryItems = document.querySelectorAll('.chat-history-item');
    chatHistoryItems.forEach(item => {
        const title = item.querySelector('span').textContent.toLowerCase();
        const sessionId = item.dataset.sessionId;
        // Fetch messages for the current session ID
        const messages = Array.from(chatWindow.children).filter(msg => {
            return msg.dataset.sessionId == sessionId;
        }).map(msg => msg.querySelector('.content').textContent.toLowerCase());
        // Check if the title or any message contains the search term
        if (title.includes(searchTerm) || messages.some(message => message.includes(searchTerm))) {
            item.style.display = ''; // Show item
        } else {
            item.style.display = 'none'; // Hide item
        }
    });
});

function editMessage(button) {
    const messageDiv = button.closest('.message');
    const contentDiv = messageDiv.querySelector('.content');
    const currentContent = contentDiv.innerText;

    // Prompt user for new content
    const newContent = prompt("Edit your message:", currentContent);
    if (newContent) {
        contentDiv.innerHTML = newContent.replace(/\n/g, '<br>'); // Update content
        // Optionally, you can also send the updated message to the server
    }
}

function deleteMessage(button) {
    const messageDiv = button.closest('.message');
    messageDiv.remove(); // Remove message from chat window
    // Optionally, you can also send a request to the server to delete the message
}

async function regenerateResponse(button) {
    const messageDiv = button.closest('.message');
    const previousMessageDiv = messageDiv.previousElementSibling; // The user message before bot reply

    if (!previousMessageDiv || !previousMessageDiv.classList.contains('user-message')) {
        alert("No user message found to regenerate response.");
        return;
    }

    const userMessage = previousMessageDiv.querySelector('.content').innerText;

    // Show typing indicator in place of current bot message
    const contentDiv = messageDiv.querySelector('.content');
    contentDiv.innerHTML = `
        <div class="typing-indicator">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    `;

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: userMessage })
        });

        const data = await response.json();

        // Replace typing indicator with new response
        let htmlContent = data.response
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/_(.*?)_/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');

        contentDiv.innerHTML = htmlContent;
    } catch (error) {
        console.error('Error regenerating response:', error);
        contentDiv.innerHTML = "<em>Failed to regenerate response. Please try again.</em>";
    }
}
