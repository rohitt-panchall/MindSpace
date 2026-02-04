// Modal and Tab functions - globally accessible
function openLoginModal() {
    const modal = document.getElementById('loginModal');
    modal.classList.add('show');
}

function closeLoginModal() {
    const modal = document.getElementById('loginModal');
    modal.classList.remove('show');
}

function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(tabName + 'Tab').classList.add('active');
    
    // Add active class to clicked button
    document.querySelector(`[onclick="switchTab('${tabName}')"]`).classList.add('active');
}

document.addEventListener('DOMContentLoaded', function() {
    const userInput = document.getElementById('userInput');
    const chatMessages = document.getElementById('chatMessages');

    function addMessage(message, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message-bubble ${isUser ? 'user' : 'bot'}`;
        messageDiv.innerHTML = `<p>${message}</p>`;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function handleKeyPress(event) {
        if (event.key === 'Enter') {
            const message = userInput.value.trim().toLowerCase();
            if (message === 'hi') {
                // Add user message
                addMessage('Hi',true);
                // Add bot response
                addMessage('Welcome to MindSpace Chatbot!', false);
                // Clear input
                userInput.value = '';
                // Redirect to chatbot page
                setTimeout(() => {
                    window.location.href = '/chatbot';
                }, 1000);
            }
        }
    }

    // Add event listener for Enter key
    userInput.addEventListener('keypress', handleKeyPress);

    // Close modal when clicking outside
    window.onclick = function(event) {
        const modal = document.getElementById('loginModal');
        if (event.target == modal) {
            closeLoginModal();
        }
    }

    // Auto-hide flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => {
                message.remove();
            }, 300);
        }, 5000);
    });
});
