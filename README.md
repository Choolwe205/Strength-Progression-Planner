# Strength Progression Planner

Strength Progression Planner is a Flask web application that helps beginner and intermediate lifters follow structured progressive overload. The app focuses on four compound movements: Bench Press, Squat, Deadlift, and Pull-ups.

Users create a profile with their body metrics and experience level. The system calculates age and BMI, generates a personalized training target for each lift, records completed workouts, adapts future targets after success or repeated failure, and visualizes progress through analytics and workout history pages.

## Features

- User registration and login with password hashing
- Automatic age and BMI calculation
- Personalized starting weights based on body weight and experience level
- Reps-first progression model for compound lifts
- Adaptive deload logic after repeated failed workouts
- Workout logging with planned versus actual performance
- Workout history grouped by date
- Analytics dashboard with strength trends, strength balance, and consistency heatmap
- Beginner and intermediate progression paths

## Progression Rules

### Beginner Starting Targets

| Exercise | Starting Rule |
|---|---|
| Bench Press | 0.50 x body weight |
| Squat | 0.75 x body weight |
| Deadlift | 0.65 x body weight |
| Pull-ups | Bodyweight, starting at 3 reps |

### Intermediate Starting Targets

| Exercise | Starting Rule |
|---|---|
| Bench Press | 0.75 x body weight |
| Squat | 1.00 x body weight |
| Deadlift | 0.80 x body weight |
| Pull-ups | Bodyweight plus added-weight progression, starting at 8 reps |

For barbell lifts, users increase reps first. Once the upper rep target is reached, the app increases weight and resets reps to the floor. Intermediate pull-ups follow the same idea, but added weight increases by 2.5 kg after the rep target is reached.

## Tech Stack

- Python
- Flask
- Flask-SQLAlchemy
- SQLite
- Jinja2 templates
- Tailwind CSS through CDN
- Chart.js through CDN
- Werkzeug password hashing

## Project Structure

```text
Strength-Progression-Planner/
  app/
    templates/
      analytics.html
      base.html
      dashboard.html
      history.html
      login.html
      profile.html
      register.html
    __init__.py
    models.py
    progression.py
    routes.py
  instance/
    strength.db
  requirements.txt
  run.py
```

## Local Setup

1. Create and activate a virtual environment.

```powershell
python -m venv venv
.\venv\Scripts\activate
```

2. Install dependencies.

```powershell
pip install -r requirements.txt
```

3. Run the app.

```powershell
python run.py
```

4. Open the app in your browser.

```text
http://127.0.0.1:5000
```

The SQLite database is created automatically in the `instance` folder when the app starts.

## Deployment Recommendation

The best free deployment option for this specific app is PythonAnywhere.

PythonAnywhere is a good match because this project is a Flask application with a small SQLite database. Render also has a free web-service tier, but Render free services use an ephemeral filesystem, so local SQLite data can be lost when the service restarts, redeploys, or spins down. That makes Render less suitable unless the app is changed to use an external database.

### Deploying on PythonAnywhere

1. Create a free PythonAnywhere account.
2. Open a Bash console on PythonAnywhere.
3. Clone your GitHub repository.

```bash
git clone https://github.com/YOUR_USERNAME/Strength-Progression-Planner.git
cd Strength-Progression-Planner
```

4. Create and activate a virtual environment.

```bash
mkvirtualenv --python=/usr/bin/python3.13 strength-planner-env
```

5. Install dependencies.

```bash
pip install -r requirements.txt
```

6. In the PythonAnywhere Web tab, create a new manual Flask web app.
7. Set the virtualenv path to:

```text
/home/YOUR_USERNAME/.virtualenvs/strength-planner-env
```

8. Edit the WSGI file and point it to the Flask app:

```python
import sys

path = '/home/YOUR_USERNAME/Strength-Progression-Planner'
if path not in sys.path:
    sys.path.insert(0, path)

from run import app as application
```

9. Reload the web app from the PythonAnywhere Web tab.
10. Visit:

```text
https://choolwebright.pythonanywhere.com/
```

## Deployment Notes

- Do not rely on `app.run()` in production hosting. PythonAnywhere loads the Flask app through the WSGI file.
- The free PythonAnywhere tier has resource limits, including one web app, one web worker, limited disk space, and account expiry rules.
- For a more production-ready deployment, move the hardcoded `SECRET_KEY` into an environment variable.
- If deploying to Render or another cloud platform, replace SQLite with a persistent hosted database such as PostgreSQL.

## Future Improvements

- Move frontend JavaScript and CSS into static files
- Add form validation and clearer API error handling
- Add automated tests for registration, login, workout logging, progression, history, and analytics
- Replace `db.create_all()` with migrations using Flask-Migrate
- Move configuration values into environment variables
- Add a first-class workout session model instead of grouping by date only
