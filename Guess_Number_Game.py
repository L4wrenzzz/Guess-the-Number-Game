from flask import Flask, render_template, request
# Flask = main to create a web app
# render_template = to render HTML from templates folder
# request = to get user input from the web app
import random # random = to generate a random number
import os

guessnumber = Flask(__name__) # create a Flask app

# global variables
attempts = 0
maxAttempts = 3
totalGames = 0
correctGuesses = 0
secretNumber = None
selected_difficulty = "easy" # Default difficulty
chosenMaxNumber = 10 #Default max number

@guessnumber.route('/', methods=['GET', 'POST'])
# @guessnumber.route('/') = the main route of the web app
# methods=['GET', 'POST'] = the route can handle both GET and POST requests
# GET = getting data from the server
# POST = sending data to the server

def index():
    global chosenMaxNumber, attempts, secretNumber, totalGames, correctGuesses, maxAttempts, selected_difficulty

    message = ""

    if request.method == 'GET' and secretNumber is None:
        secretNumber = random.randint(1, chosenMaxNumber)
        message = f'Default difficulty is easy. Guess a number between 1 and {chosenMaxNumber}.'
    difficulties = {
        'easy': 10,
        'medium': 50,
        'hard': 100,
        'impossible': 1000
    }

    if request.method == 'POST':
        form_type = request.form.get('form_type')

        # Difficulty selection function
        if form_type == 'start_game':
            message = f'Welcome to the game! Choose your difficulty above.'
            selected_difficulty = "easy"
            chosenMaxNumber = difficulties.get(selected_difficulty, 10)
            secretNumber = random.randint(1, chosenMaxNumber)
            attempts = 0 # Reset attempts when a new game starts

        elif form_type == 'set_difficulty':
            selected_difficulty = request.form.get('difficulty', 'easy')
            chosenMaxNumber = difficulties.get(selected_difficulty, 10)
            secretNumber = random.randint(1, chosenMaxNumber)
            attempts = 0 # Reset attempts when difficulty is changed
            message = f'Difficulty set to {selected_difficulty.capitalize()}. Guess a number between 1 and {chosenMaxNumber}.'

        elif form_type == 'make_guess':
            guess = request.form['guess']
            try:
                guess = int(guess) # Convert the guess to an integer
                if guess < 1 or guess > chosenMaxNumber:
                    message = f'⚠️ Please guess a number between 1 and {chosenMaxNumber}.'
                else:
                    attempts += 1 # Increment attempts for each guess
                    if guess == secretNumber:
                        message = f'✅ Nice one bro! The number was {secretNumber}.'
                        correctGuesses += 1 # Increment correct guesses
                        totalGames += 1 # Increment total games played
                        attempts = 0 # Attempts reset after a correct guess
                        secretNumber = random.randint(1, chosenMaxNumber)
                    elif attempts >= maxAttempts:
                        message = f'Game over! The number was {secretNumber}.'
                        totalGames += 1 # Increment total games played
                        attempts = 0 # Reset game
                        secretNumber = random.randint(1, chosenMaxNumber)
                    else:
                        remainingAttempts = maxAttempts - attempts
                        message = f'❌ Wrong! You have {remainingAttempts} attempts left.'
            except ValueError:
                message = '⚠️ Please enter a valid number.'
    # Determine if the game has started
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        game_started = form_type in ['start_game', 'set_difficulty', 'make_guess']
    else:
        game_started = False
    # Show the HTML page
    return render_template(
        'index.html',
        message=message,
        attempts=attempts,
        totalGames=totalGames,
        correctGuesses=correctGuesses,
        selected_difficulty=selected_difficulty,
        game_started=game_started
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    guessnumber.run(host="0.0.0.0", port=port, debug=True)