from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for
from datetime import datetime, date, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User, Workout, ProgressionLog
from app.progression import ProgressionEngine

main = Blueprint('main', __name__)
EXERCISES = ['bench', 'squat', 'deadlift', 'pullup']
KUALA_LUMPUR_TIMEZONE = timezone(timedelta(hours=8))


def to_local_datetime(timestamp):
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(KUALA_LUMPUR_TIMEZONE)


def local_date_key(timestamp):
    return to_local_datetime(timestamp).strftime('%Y-%m-%d')

# Page routes
@main.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))
    return render_template('register.html')

@main.route('/login')
def login_page():
    return render_template('login.html')

@main.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('main.index'))
    return render_template('dashboard.html')

@main.route('/analytics')
def analytics():
    if 'user_id' not in session:
        return redirect(url_for('main.index'))
    return render_template('analytics.html')

@main.route('/history')
def history():
    if 'user_id' not in session:
        return redirect(url_for('main.index'))
    return render_template('history.html')

@main.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('main.index'))
    return render_template('profile.html')

# Auth API
@main.route('/api/users', methods=['POST'])
def register_user():
    data = request.get_json()

    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already taken'}), 400

    dob = datetime.strptime(data['dob'], '%Y-%m-%d').date()
    bmi = ProgressionEngine.calculate_bmi(data['weight_kg'], data['height_cm'])
    age = ProgressionEngine.calculate_age(dob)

    user = User(
        name=data['name'],
        username=data['username'],
        password=generate_password_hash(data['password']),
        dob=dob,
        weight_kg=data['weight_kg'],
        height_cm=data['height_cm'],
        experience=data['experience'],
        bmi=bmi
    )
    db.session.add(user)
    db.session.flush()

    for exercise in EXERCISES:
        starting_weight = ProgressionEngine.get_starting_weight(
            exercise,
            data['weight_kg'],
            data['experience']
        )
        starting_reps = ProgressionEngine.get_starting_reps(
            exercise,
            data['experience']
        )
        log = ProgressionLog(
            user_id=user.id, exercise=exercise,
            current_weight=starting_weight,
            current_reps=starting_reps,
            failures=0, deload_active=False
        )
        db.session.add(log)

    db.session.commit()

    session['user_id']     = user.id
    session['user_name']   = user.name
    session['user_weight'] = user.weight_kg
    session['user_bmi']    = bmi
    session['user_age']    = age

    return jsonify({
        'message': 'User created',
        'user_id': user.id,
        'bmi': bmi,
        'age': age
    }), 201


@main.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()

    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({'error': 'Invalid username or password'}), 401

    age = ProgressionEngine.calculate_age(user.dob)
    session['user_id']     = user.id
    session['user_name']   = user.name
    session['user_weight'] = user.weight_kg
    session['user_bmi']    = user.bmi
    session['user_age']    = age

    return jsonify({
        'message': 'Login successful',
        'user_id': user.id,
        'name': user.name,
        'weight_kg': user.weight_kg,
        'bmi': user.bmi,
        'age': age
    })


@main.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out'})


# Session API
@main.route('/api/session')
def get_session():
    if 'user_id' not in session:
        return jsonify({'logged_in': False}), 401
    return jsonify({
        'logged_in': True,
        'user_id':     session['user_id'],
        'user_name':   session['user_name'],
        'user_weight': session['user_weight'],
        'user_bmi':    session['user_bmi'],
        'user_age':    session['user_age']
    })


# Workout API
@main.route('/api/workout/generate', methods=['GET'])
def generate_workout():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)
    workout = []
    for exercise in EXERCISES:
        log = ProgressionLog.query.filter_by(user_id=user_id, exercise=exercise).first()
        workout.append({
            'exercise':      exercise,
            'sets':          3,
            'reps':          log.current_reps,
            'weight':        log.current_weight,
            'deload_active': log.deload_active
        })
    return jsonify({'user': user.name, 'workout': workout})


@main.route('/api/workout/log', methods=['POST'])
def log_workout():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    data    = request.get_json()
    user_id = session['user_id']
    results = data['results']

    for result in results:
        exercise  = result['exercise']
        completed = result['completed']
        log = ProgressionLog.query.filter_by(user_id=user_id, exercise=exercise).first()

        workout = Workout(
            user_id=user_id, exercise=exercise,
            target_sets=3, target_reps=log.current_reps,
            target_weight=log.current_weight,
            actual_sets=result.get('actual_sets'),
            actual_reps=result.get('actual_reps'),
            actual_weight=result.get('actual_weight'),
            completed=completed
        )
        db.session.add(workout)

        if not completed:
            log.failures += 1
            if log.failures >= 2:
                new_weight, new_reps = ProgressionEngine.apply_deload(
                    exercise, log.current_weight, log.current_reps)
                log.current_weight = new_weight
                log.current_reps   = new_reps
                log.failures       = 0
                log.deload_active  = True
        else:
            log.deload_active = False
            new_weight, new_reps, _ = ProgressionEngine.next_progression(
                exercise, log.current_weight, log.current_reps, False)
            log.current_weight = new_weight
            log.current_reps   = new_reps
            log.failures       = 0

    db.session.commit()
    return jsonify({'message': 'Workout logged successfully'})


@main.route('/api/history')
def get_history():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    user_id = session['user_id']
    workouts = Workout.query.filter_by(user_id=user_id).order_by(
        Workout.timestamp.desc(),
        Workout.id.desc()
    ).all()

    grouped = {}
    for workout in workouts:
        date_key = local_date_key(workout.timestamp)
        grouped.setdefault(date_key, []).append({
            'exercise':      workout.exercise,
            'target_sets':   workout.target_sets,
            'target_reps':   workout.target_reps,
            'target_weight': workout.target_weight,
            'actual_sets':   workout.actual_sets,
            'actual_reps':   workout.actual_reps,
            'actual_weight': workout.actual_weight,
            'completed':     workout.completed
        })

    return jsonify({'history': grouped})


# Analytics API
@main.route('/api/analytics/<int:user_id>', methods=['GET'])
def get_analytics(user_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    if user_id != session['user_id']:
        return jsonify({'error': 'Forbidden'}), 403

    user = User.query.get_or_404(user_id)
    analytics = {}
    workout_dates = set()
    for exercise in EXERCISES:
        workouts = Workout.query.filter_by(
            user_id=user_id, exercise=exercise
        ).order_by(Workout.timestamp).all()
        workout_dates.update(local_date_key(w.timestamp) for w in workouts)
        analytics[exercise] = [{
            'date':           local_date_key(w.timestamp),
            'weight':         w.actual_weight,
            'reps':           w.actual_reps,
            'completed':      w.completed,
            'strength_ratio': round(w.actual_weight / user.weight_kg, 2) if w.actual_weight else None
        } for w in workouts]
    return jsonify({
        'user':        user.name,
        'body_weight': user.weight_kg,
        'analytics':   analytics,
        'workout_dates': sorted(workout_dates)
    })
    
    
