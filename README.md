# MindSpace Chatbot

A mental health support chatbot built with Flask, MongoDB, and Google's Gemini AI.

## Features

- User authentication (register/login)
- Chat interface with AI responses
- Session management
- Secure password hashing
- Responsive web interface

## Prerequisites

- Python 3.7+
- MongoDB Atlas account
- Google Gemini API key

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/mindspace-chatbot.git
   cd mindspace-chatbot
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory with the following content:
   ```
   MONGODB_URI=your_mongodb_connection_string
   DB_NAME=mental_health_chatbot
   GEMINI_API_KEY=your_gemini_api_key
   SECRET_KEY=your_secret_key_here
   ```

4. Run the application:
   ```
   python app.py
   ```

5. Open your browser and go to `http://127.0.0.1:5000/`

## Project Structure

- `app.py` - Main Flask application
- `database.py` - Database connection and operations
- `config.py` - Configuration settings
- `templates/` - HTML templates
- `static/` - CSS, JavaScript, and other static files

## License

This project is licensed under the MIT License - see the LICENSE file for details.
