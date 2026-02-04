import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
DB_NAME = os.getenv('DB_NAME', 'mental_health_chatbot')

# Gemini API Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyDJUAFArSiPqaaOGv3l8aIL1bOuAF7dmEM')

# Flask Configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here') 