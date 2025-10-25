from flask import Flask, render_template, request, session
import random, os, time, json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

LEADERBOARD_FILE = 'leaderboard.json'

DIFFICULTY_SETTINGS = {
    'easy': {'max_number': 10, 'max_attempts': 3, 'points': 3},
    'medium': {'max_number': 50, 'max_attempts': 8, 'points': 9},
    'hard': {'max_number': 100, 'max_attempts': 13, 'points': 17},
    'impossible': {'max_number': 1000, 'max_attempts': 25, 'points': 40},
}

TITLES = [
    ("Newbie", 20),
    ("Rookie", 100),
    ("Pro", 250),
    ("Legend", 1000),
    ("Champion", 3000)
]

def load_scores():
    if not os.path.exists(LEADERBOARD_FILE):
        return {}
    try:
        with open(LEADERBOARD_FILE, 'r') as f:
            content = f.read()
            if not content:
                return {}
            return json.loads(content)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_score(username, points, won=False):
    scores = load_scores()
    if username not in scores:
        scores[username] = {"points": 0, "correct_guesses": 0, "total_games": 0}
    scores[username]["total_games"] += 1
    if won:
        scores[username]["points"] += points
        scores[username]["correct_guesses"] += 1
    with open(LEADERBOARD_FILE, 'w') as f:
        json.dump(scores, f, indent=4)

def get_leaderboard():
    scores = load_scores()
    score_list = [(name, data.get("points", 0)) for name, data in scores.items()]
    score_list.sort(key=lambda x: x[1], reverse=True)
    return score_list

def reset_game():
    settings = DIFFICULTY_SETTINGS[session['difficulty']]
    session['random_number'] = random.randint(1, settings['max_number'])
    session['attempts'] = 0
    session['game_ready'] = False
    session.pop('start_time', None)
    session.pop('guess_history', None)

def check_guess(guess):
    settings = DIFFICULTY_SETTINGS[session['difficulty']]
    correct = session['random_number']
    session.setdefault('guess_history', []).append(guess)
    session.modified = True
    if guess < 1 or guess > settings['max_number']:
        return f"⚠️ Please guess a number between 1 and {settings['max_number']}."
    session['attempts'] += 1
    if guess == correct:
        time_taken = int(time.time() - session.get('start_time', time.time()))
        session['points'] += settings['points']
        session['total_games'] += 1
        session['correct_guesses'] += 1
        message = f"✅ Nice one, {session['username']}!\nYou guessed it in {time_taken} seconds!\nThe number was {correct}."
        save_score(session['username'], settings['points'], won=True)
        reset_game()
        return message
    elif session['attempts'] >= settings['max_attempts']:
        session['total_games'] += 1
        message = f"❌ Game over! The number was {correct}."
        save_score(session['username'], 0, won=False)
        reset_game()
        return message
    else:
        remaining = settings['max_attempts'] - session['attempts']
        hint = "⬆️ Try higher number." if guess < correct else "⬇️ Try lower number."
        return f"❌ Wrong! You have {remaining} attempts left. {hint}"

def init_session():
    session.setdefault('username', '')
    session.setdefault('points', 0)
    session.setdefault('total_games', 0)
    session.setdefault('correct_guesses', 0)
    session.setdefault('difficulty', 'easy')
    session.setdefault('attempts', 0)
    session.setdefault('game_ready', False)

def get_title(points):
    for title, threshold in reversed(TITLES):
        if points >= threshold:
            return title
    return ""

@app.route('/', methods=['GET','POST'])
def main():
    init_session()
    message = ""
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        if form_type == 'go_back':
            session.clear()
            return render_template('index.html', intro=True)
        if form_type == 'set_username':
            session['username'] = request.form.get('username', '').strip()[:12]
            scores = load_scores()
            if session['username'] in scores:
                user_data = scores[session['username']]
                session['points'] = user_data.get('points', 0)
                session['total_games'] = user_data.get('total_games', 0)
                session['correct_guesses'] = user_data.get('correct_guesses', 0)
            else:
                session['points'] = 0
                session['total_games'] = 0
                session['correct_guesses'] = 0
            session['game_ready'] = False
        if form_type == 'start_guessing':
            reset_game()
            session['start_time'] = time.time()
            session['game_ready'] = True
            session['guess_history'] = []
        elif form_type == 'make_guess':
            try:
                guess = int(request.form['guess'])
                message = check_guess(guess)
            except ValueError:
                message = "⚠️ Please enter a valid number."
        elif form_type == 'set_difficulty':
            session['difficulty'] = request.form.get('difficulty', 'easy')
            reset_game()
            message = f"Difficulty set to {session['difficulty'].capitalize()}. Click Start Game to begin."
    leaderboard = get_leaderboard()
    intro = False if session.get('username') else True
    timer = int(time.time() - session['start_time']) if session.get('start_time') and session.get('game_ready') else 0
    return render_template('index.html',
        intro=intro, username=session.get('username',''), points=session.get('points',0),
        total_games=session.get('total_games',0), correct_guesses=session.get('correct_guesses', 0),
        difficulty=session.get('difficulty','easy'), game_ready=session.get('game_ready',False),
        leaderboard=leaderboard, message=message, get_title=get_title, titles=TITLES, timer=timer,
        guess_history=session.get('guess_history', [])
    )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)