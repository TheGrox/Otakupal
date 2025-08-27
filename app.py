# app.py (Updated for Authentication with Email)
import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from services.groq_service import get_llama_response
from services.jikan_service import get_anime_data
from services.db_service import (
    save_message,
    get_messages_for_session,
    delete_chat_session, update_session_title,
    create_user, get_user_by_username, get_user_by_email, # Added get_user_by_email
    get_chat_sessions_for_user,
    create_new_chat_session_for_user
)
from dotenv import load_dotenv
import re
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()
print("GROQ_API_KEY:", os.environ.get('GROQ_API_KEY'))
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'supersecretkey')

# --- Authentication Routes ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email'] # Get email from form
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        if get_user_by_username(username):
            flash('Username already exists. Please choose a different one.', 'error')
            return render_template('register.html')
        
        if get_user_by_email(email): # Check if email already exists
            flash('Email already registered. Please use a different one or log in.', 'error')
            return render_template('register.html')

        user_id = create_user(username, email, hashed_password) # Pass email to create_user
        if user_id:
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Registration failed. Please try again.', 'error')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form['username_or_email'] # Changed input name
        password = request.form['password']
        
        user = get_user_by_username(username_or_email)
        if not user: # If not found by username, try by email
            user = get_user_by_email(username_or_email)

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username/email or password.', 'error') # Updated message
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('current_chat_id', None)
    session.pop('chat_messages', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# --- Helper for Authentication Check ---
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Chatbot Routes (Modified for Authentication) ---
@app.route('/')
@login_required
def index():
    user_id = session['user_id']
    # Initialize a new session for the user if none exists or if current_chat_id is not valid for this user
    if 'current_chat_id' not in session:
        session['current_chat_id'] = create_new_chat_session_for_user(user_id)
        session['chat_messages'] = [] # Initialize messages for the new session
    
    current_chat_id = session.get('current_chat_id')
    
    # Ensure the current_chat_id belongs to the logged-in user
    # This is a crucial security check
    user_chat_sessions = get_chat_sessions_for_user(user_id)
    valid_chat_ids = [s['id'] for s in user_chat_sessions]

    if current_chat_id not in valid_chat_ids:
        # If the current chat ID in session is not valid for this user, create a new one
        session['current_chat_id'] = create_new_chat_session_for_user(user_id)
        session['chat_messages'] = []
        current_chat_id = session['current_chat_id']

    chat_history = get_chat_sessions_for_user(user_id) # Fetch only user's chat history
    
    # Fetch messages for the current chat ID to display on initial load
    current_chat_messages = get_messages_for_session(current_chat_id)
    session['chat_messages'] = current_chat_messages # Ensure session also has these messages

    return render_template(
        'index.html',
        chat_history=chat_history,
        current_chat_id=current_chat_id,
        current_chat_messages=current_chat_messages,
        username=session['username'] # Pass username to template
    )

@app.route('/chat', methods=['POST'])
@login_required
def chat():
    user_message = request.json['message']
    user_id = session['user_id']
    current_chat_id = session.get('current_chat_id')

    # Ensure chat session is valid for this user
    valid_chat_ids = [s['id'] for s in get_chat_sessions_for_user(user_id)]
    if not current_chat_id or current_chat_id not in valid_chat_ids:
        current_chat_id = create_new_chat_session_for_user(user_id)
        session['current_chat_id'] = current_chat_id
        session['chat_messages'] = []

    # Save new user message
    save_message(current_chat_id, 'user', user_message)

    # Fetch conversation history (only keep last N messages for context)
    full_history = get_messages_for_session(current_chat_id)
    max_history = 15
    trimmed_history = full_history[-max_history:] if len(full_history) > max_history else full_history

    # Convert DB messages into Groq-compatible format
    messages_for_llm = []
    for msg in trimmed_history:
        role = 'assistant' if msg['sender'] == 'bot' else 'user'
        messages_for_llm.append({"role": role, "content": msg['content']})

    # Inject anime info context if detected
    anime_query = detect_anime_query(user_message)
    if anime_query:
        anime_data = get_anime_data(anime_query)
        if anime_data:
            context = f"User asked about: {anime_data['title']}\nAnime Data: {str(anime_data)}"
            messages_for_llm.append({"role": "system", "content": context})

    # Generate bot response
    response_content = get_llama_response(messages_for_llm)
    save_message(current_chat_id, 'bot', response_content)

    # If this is the very first user message in session, set a title
    if len(full_history) == 1:
        suggested_title = user_message[:50] + "..." if len(user_message) > 50 else user_message
        update_session_title(current_chat_id, suggested_title)
        return jsonify({
            'response': response_content,
            'current_chat_id': current_chat_id,
            'refresh_history': True
        })

    return jsonify({
        'response': response_content,
        'current_chat_id': current_chat_id,
        'refresh_history': False
    })

@app.route('/new_chat', methods=['POST'])
@login_required
def new_chat():
    user_id = session['user_id']
    new_session_id = create_new_chat_session_for_user(user_id)
    session['current_chat_id'] = new_session_id
    session['chat_messages'] = []
    return jsonify({'success': True, 'new_chat_id': new_session_id})

@app.route('/get_chat_sessions', methods=['GET'])
@login_required
def get_all_chat_sessions():
    user_id = session['user_id']
    sessions = get_chat_sessions_for_user(user_id)
    for s in sessions:
        s['created_at'] = s['created_at'].isoformat()
    return jsonify({'sessions': sessions})

@app.route('/load_chat/<int:session_id>', methods=['GET'])
@login_required
def load_chat(session_id):
    user_id = session['user_id']
    user_sessions = get_chat_sessions_for_user(user_id)
    if session_id not in [s['id'] for s in user_sessions]:
        return jsonify({'success': False, 'message': 'Unauthorized access to chat session.'}), 403

    messages = get_messages_for_session(session_id)
    session['current_chat_id'] = session_id
    session['chat_messages'] = messages
    return jsonify({'success': True, 'messages': messages, 'current_chat_id': session_id})

@app.route('/delete_chat/<int:session_id>', methods=['DELETE'])
@login_required
def delete_chat(session_id):
    user_id = session['user_id']
    user_sessions = get_chat_sessions_for_user(user_id)
    if session_id not in [s['id'] for s in user_sessions]:
        return jsonify({'success': False, 'message': 'Unauthorized deletion of chat session.'}), 403

    success = delete_chat_session(session_id)
    if success:
        if session.get('current_chat_id') == session_id:
            new_current_chat_id = create_new_chat_session_for_user(user_id)
            session['current_chat_id'] = new_current_chat_id
            session['chat_messages'] = []
            return jsonify({'success': True, 'new_current_chat_id': new_current_chat_id})
        else:
            return jsonify({'success': True, 'new_current_chat_id': session.get('current_chat_id')})
    return jsonify({'success': False}), 500

def detect_anime_query(text):
    patterns = [
        r"(?:anime|show|series) (.+?)(?:\?|$)",
        r"about (.+?)(?: anime)?$",
        r"details (?:for|on) (.+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None

if __name__ == "__main__":
    app.run(debug=True)