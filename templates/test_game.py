import unittest
from app import check_guess, DIFFICULTY_SETTINGS, session, save_score, get_leaderboard, app
import os, json

class TestGuessNumberGame(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        with app.test_request_context():
            session.clear()
            session['difficulty'] = 'easy'
            session['random_number'] = 5
            session['attempts'] = 0
            session['correct_guesses'] = 0
            session['points'] = 0
            session['total_games'] = 0
            session['username'] = 'TestPlayer'

        # Temporary leaderboard
        self.leaderboard_file = 'leaderboard.json'
        if os.path.exists(self.leaderboard_file):
            os.rename(self.leaderboard_file, self.leaderboard_file + ".bak")

    def tearDown(self):
        if os.path.exists(self.leaderboard_file):
            os.remove(self.leaderboard_file)
        if os.path.exists(self.leaderboard_file + ".bak"):
            os.rename(self.leaderboard_file + ".bak", self.leaderboard_file)

    def test_correct_guess(self):
        with app.test_request_context():
            msg, result = check_guess(5)
            self.assertTrue(result)
            self.assertIn("✅", msg)
            self.assertEqual(session['correct_guesses'], 1)
            self.assertEqual(session['points'], DIFFICULTY_SETTINGS['easy']['points'])
            self.assertEqual(session['total_games'], 1)

    def test_wrong_guess_under_attempt(self):
        with app.test_request_context():
            session['random_number'] = 5
            session['attempts'] = 0
            session['difficulty'] = 'easy'
            msg, result = check_guess(3)
            self.assertFalse(result)
            self.assertIn("Wrong!", msg)
            self.assertEqual(session['attempts'], 1)