from flask import Flask, render_template, request, session
import random, os, time

app = Flask(__name__)
app.secret_key = 'secret001'

def save_score(username, score):
    scores = {}

    if os.path.exists('leaderboard.txt'):
        with open('leaderboard.txt', 'r') as file:
            for line in file:
                name, pts = line.strip().split(',')
                scores[name] = int(pts)

    if username in scores:
        scores[username] += score
    else:
        scores[username] = score

    with open('leaderboard.txt', 'w') as file:
        for name, pts in scores.items():
            file.write(f"{name},{pts}\n")

def get_leaderboard():
    try:
        with open('leaderboard.txt', 'r') as file:
            lines = file.readlines()
        scores = [line.strip().split(',') for line in lines if ',' in line]
        scores_dict = {}
        for name, pts in scores:
            scores_dict[name] = scores_dict.get(name, 0) + int(pts)
        sorted_scores = sorted(scores_dict.items(), key=lambda x: x[1], reverse=True)
        return sorted_scores[:100]
    except FileNotFoundError:
        return []

DIFFICULTY_SETTINGS = {
    'easy': {'max_number': 10, 'max_attempts': 3, 'points': 3},
    'medium': {'max_number': 50, 'max_attempts': 8, 'points': 8},
    'hard': {'max_number': 100, 'max_attempts': 13, 'points': 13},
    'impossible': {'max_number': 1000, 'max_attempts': 25, 'points': 40},
}

@app.route('/', methods=['GET', 'POST'])
def main():
    message = ""
    leaderboard = get_leaderboard()
    timer = 0

    for key, default in {
        'totalGames': 0,
        'correctGuesses': 0,
        'points': 0,
        'difficulty': 'easy',
        'attempts': 0,
        'username': '',
        'game_started': False,
        'game_ready': False,
    }.items():
        if key not in session:
            session[key] = default

    if session.get('start_time'):
        timer = int(time.time() - session['start_time'])

    if 'randomNumber' not in session:
        settings = DIFFICULTY_SETTINGS[session['difficulty']]
        session['randomNumber'] = random.randint(1, settings['max_number'])

    if request.method == 'POST':
        form_type = request.form.get('form_type')
        session['username'] = request.form.get('username', session['username'])

        if form_type == 'go_back':
            session['game_started'] = False
            session['game_ready'] = False
            session['difficulty'] = 'easy'
            session['attempts'] = 0
            session.pop('randomNumber', None)
            session.pop('start_time', None)
            return render_template('index.html', **get_template_context(message, leaderboard, timer))

        elif form_type == 'start_game':
            session['game_started'] = True
            session['game_ready'] = False

        elif form_type == 'set_difficulty':
            selected = request.form.get('difficulty', 'easy')
            session['difficulty'] = selected
            session['attempts'] = 0
            session['game_ready'] = False
            message = f"Difficulty set to {selected.capitalize()}. Click Start Game to begin."

        elif form_type == 'start_guessing':
            settings = DIFFICULTY_SETTINGS[session['difficulty']]
            session['randomNumber'] = random.randint(1, settings['max_number'])
            session['attempts'] = 0
            session['start_time'] = time.time()
            session['game_ready'] = True
            message = f"Game started! Guess a number between 1 and {settings['max_number']}."

        elif form_type == 'make_guess':
            try:
                settings = DIFFICULTY_SETTINGS[session['difficulty']]
                guess = int(request.form['guess'])
                correct = session['randomNumber']

                if guess < 1 or guess > settings['max_number']:
                    message = f"⚠️ Please guess a number between 1 and {settings['max_number']}."
                    return render_template("index.html",
                        correctGuesses=session.get('correctGuesses', 0),
                        game_started=True,
                        game_ready=True,
                        leaderboard=get_leaderboard(),
                        message=message,
                        selected_difficulty=session.get('difficulty'),
                        timer=timer,
                        totalGames=session.get('totalGames', 0),
                        username=session.get('username'),
                    )
                
                session['attempts'] += 1

                if guess == correct:
                    timeTaken = int(time.time() - session.get('start_time', time.time()))
                    session['correctGuesses'] += 1
                    session['points'] += settings['points']
                    session['totalGames'] += 1
                    message = f"✅ Nice one, {session['username']}! You guessed it in {timeTaken} seconds! The number was {correct}."
                    save_score(session['username'], session['points'])
                    session['game_ready'] = False
                    session.pop('start_time', None)
                    session['randomNumber'] = random.randint(1, settings['max_number'])
                    session['attempts'] = 0

                elif session['attempts'] >= settings['max_attempts']:
                    message = f"Game over! The number was {correct}."
                    session['totalGames'] += 1
                    session['game_ready'] = False
                    session.pop('start_time', None)
                    session['randomNumber'] = random.randint(1, settings['max_number'])
                    session['attempts'] = 0

                else:
                    remaining = settings['max_attempts'] - session['attempts']
                    hint = "⬆️ Try higher number." if guess < correct else "⬇️ Try lower number."
                    message = f"❌ Wrong! You have {remaining} attempts left. {hint}"

            except ValueError:
                message = "⚠️ Please enter a valid number."

    return render_template('index.html', **get_template_context(message, leaderboard, timer))

def get_template_context(message, leaderboard, timer):
    return {
        'attempts': session['attempts'],
        'correctGuesses': session['correctGuesses'],
        'game_started': session['game_started'],
        'game_ready': session['game_ready'],
        'leaderboard': leaderboard,
        'message': message,
        'selected_difficulty': session['difficulty'],
        'totalGames': session['totalGames'],
        'timer': timer,
        'username': session['username'],
    }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)