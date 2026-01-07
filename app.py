import ollama
import requests
import random
from datetime import datetime
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import firebase_admin
from firebase_admin import credentials, db, auth
import uuid

app = Flask(__name__)
app.secret_key = 'srec_demo_secret_2025'

# Firebase setup
cred = credentials.Certificate("october11-868ab-firebase-adminsdk-fbsvc-38f180ff70.json")

firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://october11-868ab-default-rtdb.firebaseio.com/'
})

FIREBASE_API_KEY = "AIzaSyCS_00jpLwOXDuSoPK8pRhJL9jbzwC5-wc"

# --- Knowledge Base ---
SREC_KNOWLEDGE = {
    'about srec': "SREC, Coimbatore, est. 1994, NAAC A+ accredited, offers 12 UG, 7 PG, MBA.",
    'library': "35,000+ sq ft, 70,000+ books, 28,000+ titles.",
    'placement': "Dedicated CDP ensures strong campus placements.",
    'incubation': "SREC SPARK supports student entrepreneurs.",
    'hostel': "Well-equipped hostels for boys & girls.",
    'courses': "12 UG, 7 PG, MBA with industry focus.",
    'exam pattern': "CBCS with internal + external assessment.",
    'cse syllabus': "Visit srec.ac.in/cse for full syllabus.",
    'exam date': "Semester exams: Nov 15 - Dec 5, 2025.",
}

# --- Study Plans ---
STUDY_PLANS = {
    'cse': {
        'dbms': "1. ER Model 2. Normalization 3. SQL 4. Transactions 5. Indexing",
        'os': "1. Process Scheduling 2. Memory Mgmt 3. File Systems 4. Deadlocks"
    },
    'ece': {
        'signals': "1. Fourier 2. Laplace 3. Z-Transform 4. Sampling",
        'vlsi': "1. CMOS 2. Layout 3. Verilog 4. Fabrication"
    }
}

# --- Emotion Keywords ---
EMOTION_KEYWORDS = {
    'stressed': ['stressed', 'tired', 'overwhelmed', 'can\'t handle', 'burnt out'],
    'sad': ['sad', 'depressed', 'hopeless', 'alone', 'failed'],
    'anxious': ['anxious', 'nervous', 'worried', 'panic', 'scared']
}

def get_emotion_response(msg):
    msg = msg.lower()
    for emotion, keywords in EMOTION_KEYWORDS.items():
        if any(k in msg for k in keywords):
            responses = {
                'stressed': "I sense you're stressed. Take a break, talk to someone. You're doing great.",
                'sad': "I'm sorry you're feeling this way. You're not alone. Reach out to a friend or counselor.",
                'anxious': "It's okay to feel anxious. Breathe deep. You've overcome challenges before."
            }
            return responses[emotion] + " Visit srec.ac.in/support for help."
    return None

def get_study_plan(msg, role):
    msg = msg.lower()
    if 'study' in msg and 'cse' in role:
        if 'dbms' in msg: return f"DBMS Study Plan: {STUDY_PLANS['cse']['dbms']}"
        if 'os' in msg: return f"OS Study Plan: {STUDY_PLANS['cse']['os']}"
    return None

def verify_password(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    resp = requests.post(url, json=payload)
    return resp.json()

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        userid = request.form.get('userid')
        password = request.form.get('password')
        result = verify_password(userid, password)
        if 'idToken' in result:
            try:
                user = auth.get_user_by_email(userid)
                role = user.custom_claims.get('role', 'student') if user.custom_claims else 'student'
                session['user'] = user.uid
                session['email'] = user.email
                session['role'] = role
                return redirect(url_for('dashboard'))
            except Exception as e:
                error = f"Login failed: {str(e)}"
        else:
            error = "Login failed: Invalid email or password."
    return render_template('login.html', error=error)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        userid = request.form.get('userid')
        password = request.form.get('password')
        role = request.form.get('role', 'student')
        
        if not userid or not password:
            return render_template('signup.html', error='Email and password required')
        
        try:
            user = auth.create_user(email=userid, password=password)
            auth.set_custom_user_claims(user.uid, {'role': role})
            session['user'] = user.uid
            session['email'] = user.email
            session['role'] = role
            return redirect(url_for('dashboard'))
        except Exception as e:
            return render_template('signup.html', error=f'Signup failed: {str(e)}')
    
    return render_template('signup.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')
    
    ref = db.reference('/posts')
    posts = ref.get() or {}
    user_email = session.get('email')
    role = session.get('role')
    user_posts_count = sum(1 for p in posts.values() if p.get('user') == user_email)
    
    events = [
        {'title': 'Review Day', 'desc': 'Mini-project review on Oct 11.'},
        {'title': 'Exam Week', 'desc': 'Semester exams from Nov 15.'}
    ]
    
    return render_template(
        'dashboard.html',
        user=user_email,
        role=role,
        posts=posts,
        post_count=user_posts_count,
        events=events
    )

@app.route('/chat', methods=['POST'])
def chat():
    msg = request.json['message']
    role = session.get('role', 'student')
    msg_lower = msg.lower()

    # 1. Emotion Detection
    emotion_response = get_emotion_response(msg)
    if emotion_response:
        return jsonify({'response': emotion_response})

    # 2. Study Assistant
    study_response = get_study_plan(msg, role)
    if study_response:
        return jsonify({'response': study_response})

    # 3. Tamil-English Code-Switching
    tamil_words = ['enna', 'sir', 'pa', 'panra', 'exam', 'assignment', 'date', 'timing']
    if any(word in msg_lower for word in tamil_words):
        return jsonify({'response': "We are training the model yet."})

    # 4. SREC Knowledge Base
    for key, value in SREC_KNOWLEDGE.items():
        if key in msg_lower:
            return jsonify({'response': value})

    # 5. Fallback to LLM
    prompt = f"USER ({role}) asks: {msg}\nAnswer briefly as SREC bot."
    try:
        response = ollama.chat(model='phi3:mini', messages=[{'role': 'user', 'content': prompt}])
        return jsonify({'response': response['message']['content']})
    except Exception:
        return jsonify({'response': 'AI backend error. Ollama not running?'})

@app.route('/widget')
def widget():
    return render_template('chat_widget.html')

@app.route('/add_post', methods=['POST'])
def add_post():
    if 'user' not in session:
        return jsonify({'success': False, 'msg': 'Not logged in'}), 401

    data = request.get_json() or {}
    content = data.get('content', '').strip()
    timestamp = data.get('timestamp') or datetime.now().strftime('%Y-%m-%d %H:%M')

    if not content:
        return jsonify({'success': False, 'msg': 'Content is empty'}), 400

    user_email = session.get('email')
    ref = db.reference('/posts')
    post_id = str(uuid.uuid4())

    ref.child(post_id).set({
        'user': user_email,
        'content': content,
        'timestamp': timestamp,
        'likes': {},
        'comments': []
    })

    return jsonify({'success': True, 'post_id': post_id})

@app.route('/like_post', methods=['POST'])
def like_post():
    if 'user' not in session:
        return jsonify({'success': False}), 401

    data = request.get_json() or {}
    post_id = data.get('post_id')
    user_email = session.get('email')

    if not post_id:
        return jsonify({'success': False}), 400

    post_ref = db.reference(f'/posts/{post_id}/likes')
    likes = post_ref.get() or {}

    if user_email in likes:
        likes.pop(user_email)
    else:
        likes[user_email] = True

    post_ref.set(likes)
    return jsonify({'success': True, 'likes': len(likes)})

@app.route('/comment_post', methods=['POST'])
def comment_post():
    if 'user' not in session:
        return jsonify({'success': False}), 401

    data = request.get_json() or {}
    post_id = data.get('post_id')
    comment = data.get('comment', '').strip()
    timestamp = data.get('timestamp') or datetime.now().strftime('%Y-%m-%d %H:%M')

    if not post_id or not comment:
        return jsonify({'success': False}), 400

    user_email = session.get('email')
    comments_ref = db.reference(f'/posts/{post_id}/comments')
    comments = comments_ref.get() or []

    comments.append({
        'user': user_email,
        'comment': comment,
        'timestamp': timestamp
    })
    comments_ref.set(comments)

    return jsonify({'success': True})

@app.route('/delete_post', methods=['POST'])
def delete_post():
    if 'user' not in session:
        return jsonify({'success': False, 'msg': 'Not logged in'}), 401

    data = request.get_json() or {}
    post_id = data.get('post_id')
    if not post_id:
        return jsonify({'success': False, 'msg': 'Missing post id'}), 400

    user_email = session.get('email')
    role = session.get('role', 'student')

    post_ref = db.reference(f'/posts/{post_id}')
    post = post_ref.get()
    if not post:
        return jsonify({'success': False, 'msg': 'Post not found'}), 404

    if post.get('user') != user_email and role != 'admin':
        return jsonify({'success': False, 'msg': 'Not authorized'}), 403

    post_ref.delete()
    return jsonify({'success': True})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
