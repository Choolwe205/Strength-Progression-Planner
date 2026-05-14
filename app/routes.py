from flask import Blueprint, request, jsonify
from datetime import datetime, date
from app import db
from app.models import User, Workout, ProgressionLog
from app.progression import ProgressionEngine

main = Blueprint('main', __name__)

EXERCISES = ['bench', 'squat', 'deadlift', 'pullup']

# ── Register user ──────────────────────────────────────────
@main.route('/api/users', methods=['POST'])
def register_user():
    data = request.get_json()
    dob = datetime.strptime(data['dob'], '%Y-%m-%d').date()
    bmi = ProgressionEngine.calculate_bmi(data['weight_kg'], data['height_cm'])
    age = ProgressionEngine.calculate_age(dob)

    user = User(
        name=data['name'], dob=dob,
        weight_kg=data['weight_kg'], height_cm=data['height_cm'],
        experience=data['experience'], bmi=bmi
    )
    db.session.add(user)
    db.session.flush()

    for exercise in EXERCISES:
        starting_weight = ProgressionEngine.get_starting_weight(exercise, data['weight_kg'])
        starting_reps   = ProgressionEngine.get_starting_reps(exercise)
        log = ProgressionLog(
            user_id=user.id, exercise=exercise,
            current_weight=starting_weight,
            current_reps=starting_reps,
            failures=0, deload_active=False
        )
        db.session.add(log)

    db.session.commit()
    return jsonify({'message': 'User created', 'user_id': user.id, 'bmi': bmi, 'age': age}), 201


# ── Generate workout ───────────────────────────────────────
@main.route('/api/workout/generate', methods=['GET'])
def generate_workout():
    user_id = request.args.get('user_id', type=int)
    user = User.query.get_or_404(user_id)
    workout = []
    for exercise in EXERCISES:
        log = ProgressionLog.query.filter_by(user_id=user_id, exercise=exercise).first()
        workout.append({
            'exercise': exercise,
            'sets': 3,
            'reps': log.current_reps,
            'weight': log.current_weight,
            'deload_active': log.deload_active
        })
    return jsonify({'user': user.name, 'workout': workout})


# ── Log workout ────────────────────────────────────────────
@main.route('/api/workout/log', methods=['POST'])
def log_workout():
    data = request.get_json()
    user_id = data['user_id']
    results = data['results']

    for result in results:
        exercise = result['exercise']
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
                new_weight, new_reps = ProgressionEngine.apply_deload(exercise, log.current_weight, log.current_reps)
                log.current_weight = new_weight
                log.current_reps = new_reps
                log.failures = 0
                log.deload_active = True
        else:
            log.deload_active = False
            new_weight, new_reps, _ = ProgressionEngine.next_progression(
                exercise, log.current_weight, log.current_reps, False)
            log.current_weight = new_weight
            log.current_reps = new_reps
            log.failures = 0

    db.session.commit()
    return jsonify({'message': 'Workout logged successfully'})


# ── Analytics ──────────────────────────────────────────────
@main.route('/api/analytics/<int:user_id>', methods=['GET'])
def get_analytics(user_id):
    user = User.query.get_or_404(user_id)
    analytics = {}
    for exercise in EXERCISES:
        workouts = Workout.query.filter_by(
            user_id=user_id, exercise=exercise
        ).order_by(Workout.timestamp).all()
        analytics[exercise] = [{
            'date': w.timestamp.strftime('%Y-%m-%d'),
            'weight': w.actual_weight,
            'reps': w.actual_reps,
            'completed': w.completed,
            'strength_ratio': round(w.actual_weight / user.weight_kg, 2) if w.actual_weight else None
        } for w in workouts]
    return jsonify({'user': user.name, 'body_weight': user.weight_kg, 'analytics': analytics})