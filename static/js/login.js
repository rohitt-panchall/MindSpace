// Modal Functions
function openLoginModal() {
    const modal = document.getElementById('loginModal');
    modal.classList.add('show');
    setTimeout(() => {
        modal.style.display = 'block';
    }, 100);
}

function closeLoginModal() {
    const modal = document.getElementById('loginModal');
    modal.classList.remove('show');
    modal.style.display = 'none';
}

// Tab Functions
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(tabName).classList.add('active');
    
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(button => {
        button.classList.remove('active');
    });
    
    document.querySelector(`[onclick="showTab('${tabName}')"]`).classList.add('active');
}

// Form Handlers
function handleLogin(event) {
    event.preventDefault();
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    
    // TODO: Add login API call here
    console.log('Login attempt:', { email, password });
    
    // Update UI after successful login
    const loginBtn = document.querySelector('.login-btn');
    loginBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24">
                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/>
                        </svg>`;
    loginBtn.onclick = showSidebar;
    
    // Update profile info
    document.getElementById('userName').textContent = email.split('@')[0];
    document.getElementById('userEmail').textContent = email;
    
    // Close modal
    closeLoginModal();
    return false;
}

function handleSignup(event) {
    event.preventDefault();
    const name = document.getElementById('signupName').value;
    const email = document.getElementById('signupEmail').value;
    const password = document.getElementById('signupPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    
    if (password !== confirmPassword) {
        alert('Passwords do not match!');
        return false;
    }
    
    // TODO: Add signup API call here
    console.log('Signup attempt:', { name, email, password });
    
    // Switch to login tab after successful signup
    showTab('login');
    return false;
}

// Profile Sidebar Functions
function showSidebar() {
    const sidebar = document.getElementById('profileSidebar');
    sidebar.classList.add('show');
    sidebar.style.display = 'block';
}

function closeSidebar() {
    const sidebar = document.getElementById('profileSidebar');
    sidebar.classList.remove('show');
    setTimeout(() => {
        sidebar.style.display = 'none';
    }, 300);
}

function showHistory() {
    // TODO: Implement history functionality
    console.log('History button clicked');
    closeSidebar();
}

function logout() {
    // Reset UI to login state
    const loginBtn = document.querySelector('.login-btn');
    loginBtn.innerHTML = 'Login';
    loginBtn.onclick = openLoginModal;
    
    // Clear profile info
    document.getElementById('userName').textContent = 'User Name';
    document.getElementById('userEmail').textContent = 'user@example.com';
    
    // Close sidebar
    closeSidebar();
    
    // TODO: Add logout API call here
    console.log('Logout clicked');
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('loginModal');
    if (event.target == modal) {
        closeLoginModal();
    }
}
