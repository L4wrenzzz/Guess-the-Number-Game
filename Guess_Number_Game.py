from flask import Flask, render_template, request, session
import random, os, time, json

app = Flask(__name__)
app.secret_key = 'secret001'

LEADERBOARD_FILE = 'leaderboard.json'

DIFFICULTY_SETTINGS = {
    'easy': {'max_number': 10, 'max_attempts': 3, 'points': 3},
    'medium': {'max_number': 50, 'max_attempts': 8, 'points': 8},
    'hard': {'max_number': 100, 'max_attempts': 13, 'points': 13},
    'impossible': {'max_number': 1000, 'max_attempts': 25, 'points': 40},
}

TITLES = [
    ("Newbie", 10),
    ("Rookie", 50),
    ("Pro", 100),
    ("Legend", 500),
    ("Champion", 1000)
]

def save_score(username, points, won=False):
    if os.path.exists(LEADERBOARD_FILE):
        with open(LEADERBOARD_FILE, 'r') as f:
            scores = json.load(f)
    else:
        scores = {}

    if username not in scores:
        scores[username] = {"points": 0, "correct_guesses": 0, "total_games": 0}

    scores[username]["total_games"] += 1
    if won:
        scores[username]["points"] += points
        scores[username]["correct_guesses"] += 1

    with open(LEADERBOARD_FILE, 'w') as f:
        json.dump(scores, f, indent=4)

def get_leaderboard():
    if not os.path.exists(LEADERBOARD_FILE):
        return []
    with open(LEADERBOARD_FILE, 'r') as f:
        scores = json.load(f)
    score_list = [(name, data.get("points",0)) for name,data in scores.items()]
    score_list.sort(key=lambda x:x[1], reverse=True)
    return score_list

def reset_game():
    settings = DIFFICULTY_SETTINGS[session['difficulty']]
    session['random_number'] = random.randint(1, settings['max_number'])
    session['attempts'] = 0
    session['game_ready'] = False
    session.pop('start_time', None)

def check_guess(guess):
    settings = DIFFICULTY_SETTINGS[session['difficulty']]
    correct = session['random_number']
    if guess < 1 or guess > settings['max_number']:
        return f"⚠️ Please guess a number between 1 and {settings['max_number']}.", False
    session['attempts'] += 1
    if guess == correct:
        time_taken = int(time.time() - session.get('start_time', time.time()))
        session['points'] += settings['points']
        session['total_games'] += 1
        message = f"✅ Nice one, {session['username']}! You guessed it in {time_taken} seconds! The number was {correct}."
        save_score(session['username'], settings['points'], won=True)
        reset_game()
        return message, True
    elif session['attempts'] >= settings['max_attempts']:
        session['total_games'] += 1
        message = f"❌ Game over! The number was {correct}."
        save_score(session['username'], settings['points'], won=False)
        reset_game()
        return message, True
    else:
        remaining = settings['max_attempts'] - session['attempts']
        hint = "⬆️ Try higher number." if guess < correct else "⬇️ Try lower number."
        return f"❌ Wrong! You have {remaining} attempts left. {hint}", False

def init_session():
    session.setdefault('username','')
    session.setdefault('points',0)
    session.setdefault('total_games',0)
    session.setdefault('difficulty','easy')
    session.setdefault('attempts',0)
    session.setdefault('game_ready',False)

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

        if not session.get('username'):
            session['username'] = request.form.get('username','').strip()[:12]

        if form_type == 'start_guessing':
            reset_game()
            session['start_time'] = time.time()
            session['game_ready'] = True
        elif form_type == 'make_guess':
            try:
                guess = int(request.form['guess'])
                message, _ = check_guess(guess)
            except ValueError:
                message = "⚠️ Please enter a valid number."
        elif form_type == 'set_difficulty':
            session['difficulty'] = request.form.get('difficulty','easy')
            message = f"Difficulty set to {session['difficulty'].capitalize()}. Click Start Game to begin."

    leaderboard = get_leaderboard()
    intro = False if session.get('username') else True
    timer = int(time.time() - session.get('start_time', time.time())) if session.get('start_time') else 0

    return render_template('index.html',
        intro=intro,
        username=session.get('username',''),
        points=session.get('points',0),
        total_games=session.get('total_games',0),
        difficulty=session.get('difficulty','easy'),
        game_ready=session.get('game_ready',False),
        leaderboard=leaderboard,
        message=message,
        get_title=get_title,
        titles=TITLES,
        timer=timer
    )

if __name__ == '__main__':
    app.run(debug=True)