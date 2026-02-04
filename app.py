from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import google.generativeai as genai
from database import (init_db, init_db_connection, create_user, authenticate_user, get_user_by_email, 
                     save_chat_message, get_chat_history, create_chat_session,
                     get_chat_sessions)
from config import GEMINI_API_KEY, SECRET_KEY
import logging
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Initialize database connection
if not init_db_connection():
    logger.error("Failed to initialize database connection. Exiting...")
    exit(1)

# Initialize database indexes
if not init_db():
    logger.error("Failed to initialize database indexes. Exiting...")
    exit(1)

# Initialize Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
# Use gemini-flash-latest which should have better availability
model = genai.GenerativeModel('gemini-flash-latest')
logger.info("Initialized Gemini AI with model: gemini-flash-latest")

# Initialize database
try:
    init_db()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please provide both email and password')
            return redirect(url_for('home'))
        
        user = authenticate_user(email, password)
        if user:
            session['user_id'] = str(user['_id'])
            session['email'] = user['email']
            flash('Login successful!')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password')
            return redirect(url_for('home'))

@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        username = request.form.get('username')
        
        logger.debug(f"Register attempt - Email: {email}, Username: {username}")
        
        if not email or not password or not username:
            logger.debug("Registration failed: Missing email, password, or username")
            flash('Please provide email, password, and username')
            return redirect(url_for('home'))
        
        try:
            user_id = create_user(email, password, username)
            if user_id:
                logger.debug(f"Registration successful for email: {email}")
                flash('Registration successful! Please log in.')
                return redirect(url_for('home'))
            else:
                logger.debug(f"Registration failed: User creation returned None for email: {email}")
                flash('Registration failed. Email might already be registered.')
                return redirect(url_for('home'))
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            flash('An error occurred during registration.')
            return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!')
    return redirect(url_for('home'))

@app.route('/chatbot')
@login_required
def chatbot():
    try:
        # Get user information from database
        user = get_user_by_email(session.get('email'))
        if not user:
            flash('User not found.')
            return redirect(url_for('home'))
            
        # Create a new chat session if none exists
        if 'chat_session_id' not in session:
            session['chat_session_id'] = create_chat_session(str(user['_id']))
            
        return render_template('chatbot.html', user=user)
    except Exception as e:
        logger.error(f"Error in chatbot route: {str(e)}")
        flash('An error occurred. Please try again.')
        return redirect(url_for('home'))

@app.route('/features')
def features():
    return render_template('features.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/chat_history')
@login_required
def get_user_chat_history():
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
            
        # Get all chat sessions with their messages
        history = get_chat_history(user_id)
        sessions = get_chat_sessions(user_id)
        
        # Format sessions data
        formatted_sessions = []
        for sess in sessions:
            sess_id = str(sess['_id'])
            formatted_sessions.append({
                'id': sess_id,
                'created_at': sess['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
                'messages': history.get(sess_id, [])
            })
            
        return jsonify({'sessions': formatted_sessions})
    except Exception as e:
        logger.error(f"Error retrieving chat history: {str(e)}")
        return jsonify({'error': 'Failed to retrieve chat history'}), 500

@app.route('/continue_chat/<session_id>')
@login_required
def continue_chat(session_id):
    try:
        session['chat_session_id'] = session_id
        return redirect(url_for('chatbot', session_id=session_id))
    except Exception as e:
        logger.error(f"Error continuing chat: {str(e)}")
        return redirect(url_for('chatbot'))

@app.route('/get_session_messages/<session_id>')
@login_required
def get_session_messages(session_id):
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
            
        messages = get_chat_history(user_id, session_id)
        return jsonify({'messages': messages})
    except Exception as e:
        logger.error(f"Error getting session messages: {str(e)}")
        return jsonify({'error': 'Failed to get messages'}), 500

@app.route('/new_chat')
@login_required
def new_chat():
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
            
        # Create new chat session
        session['chat_session_id'] = create_chat_session(user_id)
        return redirect(url_for('chatbot'))
    except Exception as e:
        logger.error(f"Error creating new chat: {str(e)}")
        return redirect(url_for('chatbot'))

@app.route('/get_response', methods=['POST'])
@login_required
def get_response():
    user_message = request.json.get('message')
    user_id = session.get('user_id')
    chat_session_id = session.get('chat_session_id')
    
    if not user_message or not chat_session_id:
        return jsonify({"message": "Please enter a message."}), 400
    
    try:
        # Save user message to database
        save_chat_message(user_id, user_message, chat_session_id, is_user=True)
        
        # Check if message is related to mental health
        mental_health_keywords = [
            # Emotional States
            'anxiety', 'depression', 'stress', 'mental health', 'therapy', 'counseling',
            'suicide', 'self-harm', 'trauma', 'ptsd', 'mood', 'emotions', 'psychologist',
            'psychiatrist', 'coping', 'support', 'wellbeing', 'cognitive', 'mental',
            'panic', 'hopeless', 'worthless', 'guilt', 'shame', 'sad', 'crying',
            'happy', 'angry', 'mad', 'frustrated', 'stressed', 'overwhelmed', 'fear',
            'scared', 'worried', 'anxious', 'depressed', 'lonely', 'isolated', 'numb',
            'exhausted', 'tired', 'drained', 'emotional', 'feeling', 'feel', 'felt',
            
            # Mental Health Conditions
            'obsessive-compulsive disorder', 'ocd', 'adhd', 'add', 'bipolar',
            'schizophrenia', 'eating disorder', 'anorexia', 'bulimia', 'binge eating',
            'personality disorder', 'borderline', 'bpd', 'dissociation', 'ptsd',
            'trauma', 'anxiety disorder', 'panic disorder', 'phobia', 'agoraphobia',
            'social anxiety', 'generalized anxiety', 'depression', 'major depression',
            'dysthymia', 'seasonal affective disorder', 'sad', 'postpartum',
            
            # Treatment & Support
            'medication', 'meds', 'therapy', 'therapist', 'counseling', 'counselor',
            'psychiatrist', 'psychologist', 'mental health professional', 'treatment',
            'support group', 'peer support', 'self-help', 'coping skills', 'coping mechanisms',
            'mindfulness', 'meditation', 'breathing exercises', 'grounding techniques',
            'self-care', 'recovery', 'healing', 'wellness', 'wellbeing', 'help',
            'support', 'crisis', 'hotline', 'helpline', 'resources', 'diagnosis',
            
            # Symptoms & Experiences
            'insomnia', 'sleep', 'nightmare', 'flashback', 'trigger', 'triggered',
            'panic attack', 'anxiety attack', 'intrusive thoughts', 'racing thoughts',
            'overthinking', 'ruminating', 'worry', 'stress', 'burnout', 'breakdown',
            'crisis', 'suicidal thoughts', 'self-harm', 'cutting', 'substance use',
            'addiction', 'relapse', 'withdrawal', 'craving', 'urge',
            
            # Lifestyle & Coping
            'exercise', 'nutrition', 'diet', 'sleep', 'routine', 'habits',
            'journaling', 'meditation', 'yoga', 'mindfulness', 'breathing',
            'grounding', 'self-care', 'boundaries', 'relationship', 'family',
            'friend', 'work', 'school', 'stress management', 'time management',
            
            # Conversation Starters
            'hey', 'hello', 'hi', 'help', 'talk', 'listen', 'need advice',
            'struggling', 'difficult', 'hard time', 'tough time', 'going through',
            'dealing with', 'coping with', 'how to', 'what to do', 'should i',
            'can you help', 'please help', 'advice', 'suggestion', 'recommend',
            'question', 'confused', 'unsure', 'dont know', "don't know",
            
            # General Mental Health Terms
            'mental illness', 'mental disorder', 'mental condition', 'brain',
            'neurodiversity', 'neurodivergent', 'neurotypical', 'diagnosis',
            'diagnosed', 'symptoms', 'side effects', 'recovery', 'wellness',
            'wellbeing', 'health', 'healthy', 'unhealthy', 'toxic', 'trauma',
            'traumatic', 'crisis', 'emergency', 'urgent', 'immediate'
        ]
        
        # Check if any mental health keywords are present
        message_lower = user_message.lower()
        if not any(keyword in message_lower for keyword in mental_health_keywords):
            return jsonify({"message": "I'm here to help with mental health concerns. Feel free to share your thoughts, feelings, or any mental health-related questions you have. I'm here to listen and support you."}), 400
            
        # Using Gemini API with enhanced mental health focus
        try:
            response = model.generate_content(
                f"""You are a caring mental health companion. Format your responses in exactly 5 lines:

                RESPONSE STRUCTURE (4lines total):
                Line 1: Brief validation of their feelings
                Line 2: Show understanding of their situation
                Line 3: Provide one clear, practical suggestion or observation
                Line 4: End with a gentle, focused question

                GUIDELINES:
                - Keep responses STRICTLY to 4 lines
                - Use warm, simple language
                - Be specific but brief
                - For crisis mentions, include hotline info within the 5-line limit
                - Each line should be clear and complete

                User shared: '{user_message}'
                
                Respond with exactly 4 lines following the structure above."""
            )
        except Exception as api_error:
            # If the current model fails, try alternative models
            logger.warning(f"Model failed, trying alternatives: {api_error}")
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content(
                    f"""You are a caring mental health companion. Format your responses in exactly 5 lines:

                    RESPONSE STRUCTURE (4lines total):
                    Line 1: Brief validation of their feelings
                    Line 2: Show understanding of their situation
                    Line 3: Provide one clear, practical suggestion or observation
                    Line 4: End with a gentle, focused question

                    GUIDELINES:
                    - Keep responses STRICTLY to 4 lines
                    - Use warm, simple language
                    - Be specific but brief
                    - For crisis mentions, include hotline info within the 5-line limit
                    - Each line should be clear and complete

                    User shared: '{user_message}'
                    
                    Respond with exactly 4 lines following the structure above."""
                )
                logger.info("Successfully used gemini-2.5-flash as fallback")
            except Exception as fallback_error:
                logger.error(f"All model attempts failed: {fallback_error}")
                raise api_error  # Re-raise the original error
        
        # Format the response in bullet points
        bot_response = response.text
        
        # Clean the response
        cleaned_response = bot_response.replace('*', '').replace('•', '').replace('User:', '').replace('Assistant:', '').strip()
        
        # Split into points and ensure exactly 5 lines
        points = []
        for delimiter in ['. ', '\n', '; ']:
            if delimiter in cleaned_response:
                points = [point.strip() for point in cleaned_response.split(delimiter) if point.strip()][:5]
                # Ensure we have exactly 5 points
                while len(points) < 5:
                    points.append("Would you like to tell me more about that?")
                break
        
        # Format points
        formatted_points = []
        for point in points[:5]:  # Limit to exactly 5 points
            if point and not point.isspace():
                formatted_points.append(f"• {point.strip()}")
        
        # Join points with single newlines to keep response compact
        formatted_response = "\n".join(formatted_points)
        
        # Save bot response to database
        save_chat_message(user_id, formatted_response, chat_session_id, is_user=False)
        
        return jsonify({"message": formatted_response})
        
    except Exception as e:
        logger.error(f"Error in get_response: {str(e)}")
        error_msg = str(e)
        # Handle quota/rate limit errors
        if "quota" in error_msg.lower() or "429" in error_msg or "ResourceExhausted" in error_msg:
            return jsonify({"message": "API quota exceeded. Please try again later or check your API usage limits."}), 429
        # Handle API key errors
        elif "API key" in error_msg or "401" in error_msg or "403" in error_msg:
            return jsonify({"message": "API key error. Please check your Gemini API key configuration."}), 401
        else:
            return jsonify({"message": f"An error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
    