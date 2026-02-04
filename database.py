from pymongo import MongoClient
from config import MONGODB_URI, DB_NAME
import bcrypt
import logging
from datetime import datetime
from bson import ObjectId

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# MongoDB connection with more detailed error handling
def get_db_connection():
    """
    Create a MongoDB client using the URI from config.
    This supports both local MongoDB (mongodb://...) and MongoDB Atlas (mongodb+srv://...).
    """
    try:
        logger.info(f"Attempting to connect to MongoDB using URI from config")
        client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000,  # 5 second timeout
            connectTimeoutMS=5000
        )

        # Test the connection
        client.server_info()
        logger.info("Successfully connected to MongoDB")

        return client
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB using URI '{MONGODB_URI}': {str(e)}")
        raise

# Database connection will be initialized when needed
db = None
users = None
chats = None
chat_sessions = None

def init_db_connection():
    """Initialize the database connection when the app starts"""
    global db, users, chats, chat_sessions
    try:
        client = get_db_connection()
        db = client[DB_NAME]
        users = db.users
        chats = db.chats
        chat_sessions = db.chat_sessions
        logger.info(f"Successfully connected to database: {DB_NAME}")
        return True
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        return False

def refresh_connection():
    """Refresh MongoDB connection if it becomes stale"""
    global client, db, users, chats, chat_sessions
    try:
        # Test current connection
        client.server_info()
        logger.debug("Connection is still active")
    except Exception as e:
        logger.warning(f"Connection is stale, refreshing... Error: {str(e)}")
        try:
            client = get_db_connection()
            db = client[DB_NAME]
            users = db.users
            chats = db.chats
            chat_sessions = db.chat_sessions
            logger.info("Connection refreshed successfully")
        except Exception as e2:
            logger.error(f"Failed to refresh connection: {str(e2)}")
            raise

def init_db():
    """Initialize database with indexes"""
    try:
        # Make sure we have a connection
        if None in [users, chats, chat_sessions]:
            if not init_db_connection():
                return False
                
        # Create unique index on email for users
        users.create_index('email', unique=True)
        logger.info("Successfully created unique index on email field")
        
        # Create index on user_id for chats and sessions
        chats.create_index([('user_id', 1), ('session_id', 1)])
        chat_sessions.create_index('user_id')
        logger.info("Successfully created indexes for chats and sessions")
        return True
    except Exception as e:
        logger.error(f"Failed to create index: {str(e)}")
        raise

def hash_password(password):
    """Hash a password using bcrypt"""
    try:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        logger.debug("Successfully hashed password")
        return hashed
    except Exception as e:
        logger.error(f"Failed to hash password: {e}")
        raise

def verify_password(password, hashed_password):
    """Verify a password against its hash"""
    try:
        result = bcrypt.checkpw(password.encode('utf-8'), hashed_password)
        logger.debug(f"Password verification result: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to verify password: {e}")
        raise

def create_user(email, password, username):
    """Create a new user"""
    try:
        refresh_connection()  # Ensure connection is fresh
        logger.info(f"Attempting to create user with email: {email} and username: {username}")
        hashed_password = hash_password(password)
        user = {
            'email': email,
            'username': username,
            'password': hashed_password,
            'created_at': datetime.utcnow()
        }
        logger.debug(f"Attempting to insert user document: {{'email': {email}, 'username': {username}, 'password': '***'}}")
        
        # Verify database connection before insert
        client.server_info()
        logger.debug(f"Database connection verified before insert")
        
        # Get current user count
        current_count = users.count_documents({})
        logger.debug(f"Current user count in database: {current_count}")
        
        result = users.insert_one(user)
        
        # Ensure write is acknowledged
        if not result.acknowledged:
            logger.error("User insert was not acknowledged by MongoDB!")
            return None
        
        # Verify the insert
        new_count = users.count_documents({})
        logger.info(f"User count after insert: {new_count}")
        logger.info(f"Successfully created user with ID: {result.inserted_id}")
        
        # Verify the user was actually saved
        saved_user = users.find_one({'_id': result.inserted_id})
        if saved_user:
            logger.info("Successfully verified user was saved in database")
        else:
            logger.warning("User document not found after insert!")
            
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Failed to create user: {str(e)}")
        return None

def get_user_by_email(email):
    """Get user by email"""
    try:
        logger.debug(f"Looking up user with email: {email}")
        user = users.find_one({'email': email})
        if user:
            logger.debug("User found")
        else:
            logger.debug("User not found")
        return user
    except Exception as e:
        logger.error(f"Error looking up user: {e}")
        return None

def authenticate_user(email, password):
    """Authenticate a user"""
    try:
        logger.info(f"Attempting to authenticate user: {email}")
        user = get_user_by_email(email)
        if user and verify_password(password, user['password']):
            logger.info("Authentication successful")
            return user
        logger.warning("Authentication failed")
        return None
    except Exception as e:
        logger.error(f"Error during authentication: {e}")
        return None

def create_chat_session(user_id):
    """Create a new chat session"""
    try:
        refresh_connection()  # Ensure connection is fresh
        session = {
            'user_id': user_id,
            'created_at': datetime.utcnow(),
            'last_message_at': datetime.utcnow(),
            'is_active': True
        }
        result = chat_sessions.insert_one(session)
        if not result.acknowledged:
            logger.error("Chat session insert was not acknowledged by MongoDB!")
            return None
        logger.debug(f"Created new chat session for user {user_id}")
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Failed to create chat session: {str(e)}")
        return None

def get_chat_sessions(user_id):
    """Get all chat sessions for a user"""
    try:
        sessions = list(chat_sessions.find(
            {'user_id': user_id}
        ).sort('last_message_at', -1))
        return sessions
    except Exception as e:
        logger.error(f"Failed to get chat sessions: {str(e)}")
        return []

def save_chat_message(user_id, message, session_id, is_user=True):
    """Save a chat message to the database"""
    try:
        refresh_connection()  # Ensure connection is fresh
        chat_message = {
            'user_id': user_id,
            'session_id': session_id,
            'message': message,
            'is_user': is_user,
            'timestamp': datetime.utcnow()
        }
        result = chats.insert_one(chat_message)
        
        if not result.acknowledged:
            logger.error("Chat message insert was not acknowledged by MongoDB!")
            return None
        
        # Update session's last_message_at
        update_result = chat_sessions.update_one(
            {'_id': ObjectId(session_id)},
            {'$set': {'last_message_at': datetime.utcnow()}}
        )
        
        if not update_result.acknowledged:
            logger.warning("Chat session update was not acknowledged by MongoDB!")
        
        logger.debug(f"Saved chat message for user {user_id} in session {session_id}, message ID: {result.inserted_id}")
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Failed to save chat message: {str(e)}")
        return None

def get_chat_history(user_id, session_id=None):
    """Get chat history for a user, optionally filtered by session"""
    try:
        query = {'user_id': user_id}
        if session_id:
            query['session_id'] = session_id
            
        # Get messages for the specified session or all sessions
        messages = list(chats.find(
            query,
            {'_id': 0, 'message': 1, 'is_user': 1, 'timestamp': 1, 'session_id': 1}
        ).sort('timestamp', 1))
        
        # If no session_id provided, group by session
        if not session_id:
            sessions = {}
            for msg in messages:
                sess_id = str(msg['session_id'])
                if sess_id not in sessions:
                    sessions[sess_id] = []
                sessions[sess_id].append({
                    'text': msg['message'],
                    'is_user': msg['is_user'],
                    'timestamp': msg['timestamp'].isoformat()  # Use ISO format for proper timezone handling
                })
            return sessions
        else:
            # Return messages for single session
            return [{
                'text': msg['message'],
                'is_user': msg['is_user'],
                'timestamp': msg['timestamp'].isoformat()  # Use ISO format for proper timezone handling
            } for msg in messages]
            
    except Exception as e:
        logger.error(f"Failed to get chat history: {str(e)}")
        if session_id:
            return []  # Return empty list for single session
        return {}  # Return empty dict for all sessions 