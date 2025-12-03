from flask import Flask, render_template, request, session, jsonify
import random, os, time, re
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

DIFFICULTY_SETTINGS = {
    'easy':       {'max_number': 10,        'max_attempts': 3,  'points': 3},
    'medium':     {'max_number': 100,       'max_attempts': 8,  'points': 10},
    'hard':       {'max_number': 1000,      'max_attempts': 15, 'points': 20},
    'impossible': {'max_number': 100000,    'max_attempts': 25, 'points': 45},
    'million':    {'max_number': 1000000,   'max_attempts': 50, 'points': 150},
}

TITLES = [
    ("Newbie", 100),
    ("Rookie", 500),
    ("Pro", 2500),
    ("Legend", 5000),
    ("Champion", 10000)
]

def save_score(username, points_to_add, won=False):
    try:
        response = supabase.table('leaderboard').select('*').eq('username', username).execute()
        current_data = response.data[0] if response.data else {'points': 0, 'correct_guesses': 0, 'total_games': 0}

        new_total = current_data['total_games'] + 1
        new_points = current_data['points'] + points_to_add
        new_correct = current_data['correct_guesses'] + (1 if won else 0)

        supabase.table('leaderboard').upsert({
            'username': username, 'points': new_points,
            'correct_guesses': new_correct, 'total_games': new_total
        }).execute()
        
        session['points'] = new_points
        session['total_games'] = new_total
        session['correct_guesses'] = new_correct
        
    except Exception as e:
        print(f"Error saving score: {e}")

def get_title(points):
    for title, threshold in reversed(TITLES):
        if points >= threshold:
            return title
    return "Newbie"

def check_if_the_one(username, points):
    try:
        response = supabase.table('leaderboard').select('username').order('points', desc=True).limit(1).execute()
        if response.data and response.data[0]['username'] == username:
            return True
    except:
        pass
    return False

def init_session_defaults():
    defaults = {
        'points': 0, 'total_games': 0, 'correct_guesses': 0,
        'difficulty': 'easy', 'attempts': 0, 'game_ready': False,
        'guess_history': []
    }
    for k, v in defaults.items():
        session.setdefault(k, v)

@app.route('/')
def index():
    init_session_defaults()
    user_title = "Newbie"
    if session.get('username'):
        pts = session.get('points', 0)
        user_title = get_title(pts)
        if check_if_the_one(session.get('username'), pts):
            user_title = "THE ONE"

    return render_template('index.html', 
                           username=session.get('username'), 
                           user_title=user_title,
                           titles=TITLES,
                           diff_settings=DIFFICULTY_SETTINGS)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '').strip()[:12]
    
    if not username or not re.match("^[a-zA-Z0-9]+$", username):
        return jsonify({'error': 'Invalid username. Only letters and numbers allowed.'}), 400
    
    session['username'] = username
    current_title = "Newbie"
    
    try:
        response = supabase.table('leaderboard').select('*').eq('username', username).execute()
        if response.data:
            user = response.data[0]
            session['points'] = user.get('points', 0)
            session['total_games'] = user.get('total_games', 0)
            session['correct_guesses'] = user.get('correct_guesses', 0)
            current_title = get_title(session['points'])
            if check_if_the_one(username, session['points']):
                current_title = "THE ONE"
    except Exception:
        pass
        
    return jsonify({
        'success': True,
        'points': session.get('points', 0),
        'title': current_title
    })

@app.route('/api/difficulty', methods=['POST'])
def set_difficulty():
    data = request.json
    session['difficulty'] = data.get('difficulty', 'easy')
    settings = DIFFICULTY_SETTINGS[session['difficulty']]
    return jsonify({
        'message': f"Difficulty set to {session['difficulty'].capitalize()}.",
        'max_number': settings['max_number']
    })

@app.route('/api/start', methods=['POST'])
def start_game():
    settings = DIFFICULTY_SETTINGS[session['difficulty']]
    session['random_number'] = random.randint(1, settings['max_number'])
    session['attempts'] = 0
    session['game_ready'] = True
    session['start_time'] = time.time()
    session['guess_history'] = []
    
    return jsonify({
        'message': "Game Started! Good luck.",
        'game_ready': True,
        'max_number': settings['max_number']
    })

@app.route('/api/guess', methods=['POST'])
def guess():
    if not session.get('game_ready'):
        return jsonify({'error': 'Game not started'}), 400

    try:
        guess_val = int(request.json.get('guess'))
    except (ValueError, TypeError):
        return jsonify({'message': "⚠️ Please enter a valid number.", 'status': 'error'})

    settings = DIFFICULTY_SETTINGS[session['difficulty']]
    correct_num = session['random_number']
    
    history = session.get('guess_history', [])
    history.append(guess_val)
    session['guess_history'] = history
    
    if guess_val < 1 or guess_val > settings['max_number']:
        return jsonify({'message': f"⚠️ Number must be between 1 and {settings['max_number']}.", 'status': 'warning'})

    session['attempts'] += 1
    attempts_left = settings['max_attempts'] - session['attempts']
    
    if guess_val == correct_num:
        time_taken = int(time.time() - session['start_time'])
        save_score(session['username'], settings['points'], won=True)
        session['game_ready'] = False
        
        new_title = get_title(session['points'])
        if check_if_the_one(session['username'], session['points']):
            new_title = "THE ONE"

        return jsonify({
            'status': 'win',
            'message': f"✅ You guessed it in {time_taken}s! The number was {correct_num}.",
            'new_points': session['points'],
            'new_title': new_title
        })
        
    elif session['attempts'] >= settings['max_attempts']:
        save_score(session['username'], 0, won=False)
        session['game_ready'] = False
        return jsonify({
            'status': 'lose',
            'message': f"❌ Game Over! The number was {correct_num}."
        })
        
    else:
        hint = "⬆️ Higher" if guess_val < correct_num else "⬇️ Lower"
        return jsonify({
            'status': 'continue',
            'message': f"❌ Wrong. {hint}",
            'attempts_left': attempts_left,
            'history': history
        })

@app.route('/api/leaderboard')
def get_leaderboard_data():
    try:
        response = supabase.table('leaderboard').select('username', 'points').order('points', desc=True).limit(100).execute()
        data = []
        for index, p in enumerate(response.data):
            if index == 0:
                title = "THE ONE"
            else:
                title = get_title(p['points'])
            
            data.append({
                'username': p['username'],
                'points': p['points'],
                'title': title
            })
        return jsonify(data)
    except Exception as e:
        return jsonify([])

@app.route('/api/stats')
def get_stats():
    pts = session.get('points', 0)
    current_title = get_title(pts)
    if check_if_the_one(session.get('username'), pts):
        current_title = "THE ONE"

    return jsonify({
        'points': pts,
        'total_games': session.get('total_games', 0),
        'correct_guesses': session.get('correct_guesses', 0),
        'title': current_title
    })

@app.route('/logout')
def logout():
    session.clear()
    return jsonify({'success': True})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)