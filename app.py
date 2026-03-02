
# Interactive drill tracker route

from flask import Flask, render_template, request, redirect, url_for, session, flash
import csv
import os
from werkzeug.security import generate_password_hash, check_password_hash
app = Flask(__name__)
app.secret_key = 'replace_this_with_a_secret_key'

USERS_FILE = 'users.csv'
DATA_DIR = 'user_data'

# Ensure user data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

def get_user_csv(username):
    return os.path.join(DATA_DIR, f"{username}_matches.csv")

def get_user_drill_csv(username):
    return os.path.join(DATA_DIR, f"{username}_drills.csv")

# Route for advanced stats page
@app.route('/stats', methods=['GET'])
def stats():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    user_csv = get_user_csv(username)
    matches = []
    if os.path.exists(user_csv):
        with open(user_csv, 'r', newline='') as f:
            reader = csv.DictReader(f)
            matches = list(reader)
    # Prepare data for filters
    opponents = sorted(set(m['opponent'] for m in matches if m.get('opponent')))
    locations = sorted(set(m['location'] for m in matches if m.get('location')))
    game_types = sorted(set(m['game_type'] for m in matches if m.get('game_type')))
    return render_template('stats.html', matches=matches, opponents=opponents, locations=locations, game_types=game_types)

def get_user_csv(username):
    return os.path.join(DATA_DIR, f"{username}_matches.csv")

def get_user_drill_csv(username):
    return os.path.join(DATA_DIR, f"{username}_drills.csv")

def user_exists(username):
    if not os.path.exists(USERS_FILE):
        return False
    with open(USERS_FILE, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['username'] == username:
                return True
    return False

def register_user(username, password):
    new_user = not os.path.exists(USERS_FILE)
    with open(USERS_FILE, 'a', newline='') as f:
        fieldnames = ['username', 'password_hash']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if new_user:
            writer.writeheader()
        writer.writerow({'username': username, 'password_hash': generate_password_hash(password)})

def validate_login(username, password):
    if not os.path.exists(USERS_FILE):
        return False
    with open(USERS_FILE, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['username'] == username and check_password_hash(row['password_hash'], password):
                return True
    return False

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if user_exists(username):
            flash('Username already exists.')
            return redirect(url_for('register'))
        register_user(username, password)
        flash('Registration successful. Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if validate_login(username, password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Logged out successfully.')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    matches = []
    drills = []
    user_csv = get_user_csv(username)
    user_drill_csv = get_user_drill_csv(username)
    win_count = 0
    loss_count = 0
    if os.path.exists(user_csv):
        with open(user_csv, 'r', newline='') as f:
            reader = csv.DictReader(f)
            matches = list(reader)
            for match in matches:
                if match.get('result') == 'win':
                    win_count += 1
                elif match.get('result') == 'loss':
                    loss_count += 1
    if os.path.exists(user_drill_csv):
        with open(user_drill_csv, 'r', newline='') as f:
            reader = csv.DictReader(f)
            drills = list(reader)
    return render_template('dashboard.html', matches=matches, drills=drills, win_count=win_count, loss_count=loss_count)


# Add match route
@app.route('/add_match', methods=['GET', 'POST'])
def add_match():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    user_csv = get_user_csv(username)
    last_match = {'date': '', 'opponent': '', 'game_type': ''}
    if os.path.exists(user_csv):
        with open(user_csv, 'r', newline='') as f:
            reader = list(csv.DictReader(f))
            if reader:
                last = reader[-1]
                last_match = {
                    'date': last.get('date', ''),
                    'opponent': last.get('opponent', ''),
                    'location': last.get('location', ''),
                    'game_type': last.get('game_type', '')
                }
    if request.method == 'POST':
        fieldnames = ['date', 'location', 'opponent', 'game_type', 'partner', 'result']
        new_entry = {
            'date': request.form['date'],
            'location': request.form['location'],
            'opponent': request.form['opponent'],
            'game_type': request.form['game_type'],
            'partner': request.form.get('partner', 'N/A') or 'N/A',
            'result': request.form['result']
        }
        file_exists = os.path.exists(user_csv)
        with open(user_csv, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(new_entry)
        flash('Match added!')
        return redirect(url_for('dashboard'))
    return render_template('add_match.html', last_match=last_match)

# Add drill route
@app.route('/add_drill', methods=['GET', 'POST'])
def add_drill():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        username = session['username']
        user_drill_csv = get_user_drill_csv(username)
        fieldnames = ['date', 'drill_name', 'balls_made', 'balls_missed']
        new_entry = {
            'date': request.form['date'],
            'drill_name': request.form['drill_name'],
            'balls_made': request.form['balls_made'],
            'balls_missed': request.form['balls_missed']
        }
        file_exists = os.path.exists(user_drill_csv)
        with open(user_drill_csv, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(new_entry)
        flash('Drill added!')
        return redirect(url_for('dashboard'))
    return render_template('add_drill.html')

@app.route('/drill_tracker', methods=['GET', 'POST'])
def drill_tracker():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        username = session['username']
        user_drill_csv = get_user_drill_csv(username)
        fieldnames = ['date', 'drill_name', 'balls_made', 'balls_missed']
        new_entry = {
            'date': request.form['date'],
            'drill_name': request.form['drill_name'],
            'balls_made': request.form['balls_made'],
            'balls_missed': request.form['balls_missed']
        }
        file_exists = os.path.exists(user_drill_csv)
        with open(user_drill_csv, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(new_entry)
        flash('Drill result saved!')
        return redirect(url_for('dashboard'))
    return render_template('drill_tracker.html')

# Opponent log route
@app.route('/opponent_log', methods=['GET', 'POST'])
def opponent_log():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    opp_csv = os.path.join(DATA_DIR, f"{username}_opponents.csv")
    fieldnames = ['opponent', 'apa_level', 'location', 'notes']
    if request.method == 'POST':
        new_entry = {
            'opponent': request.form['opponent'],
            'location': request.form['location'],
            'apa_level': request.form['apa_level'],
            'notes': request.form['notes']
        }
        file_exists = os.path.exists(opp_csv)
        with open(opp_csv, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(new_entry)
        flash('Opponent info saved!')
        return redirect(url_for('opponent_log'))
    opponents = []
    if os.path.exists(opp_csv):
        with open(opp_csv, 'r', newline='') as f:
            reader = csv.DictReader(f)
            opponents = list(reader)
    return render_template('opponent_log.html', opponents=opponents)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
