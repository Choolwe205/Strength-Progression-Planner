from datetime import date

FORMULAS = {
    'bench':    {'multiplier': 0.40, 'increment': 2.5},
    'squat':    {'multiplier': 0.75, 'increment': 5.0},
    'deadlift': {'multiplier': 0.50, 'increment': 5.0},
    'pullup':   {'multiplier': None, 'increment': None},
}

REP_FLOOR = 6
REP_CEILING = 12
PULLUP_FLOOR = 3
PULLUP_CEILING = 10
SETS = 3
FAIL_THRESHOLD = 2
DELOAD_FACTOR = 0.75

class ProgressionEngine:

    @staticmethod
    def get_starting_weight(exercise, body_weight):
        if exercise == 'pullup':
            return None
        multiplier = FORMULAS[exercise]['multiplier']
        raw = body_weight * multiplier
        return round(raw * 2) / 2

    @staticmethod
    def get_starting_reps(exercise):
        return PULLUP_FLOOR if exercise == 'pullup' else REP_FLOOR

    @staticmethod
    def calculate_bmi(weight_kg, height_cm):
        height_m = height_cm / 100
        return round(weight_kg / (height_m ** 2), 1)

    @staticmethod
    def calculate_age(dob):
        today = date.today()
        return today.year - dob.year - (
            (today.month, today.day) < (dob.month, dob.day)
        )

    @staticmethod
    def next_progression(exercise, current_weight, current_reps, failed):
        ceiling = PULLUP_CEILING if exercise == 'pullup' else REP_CEILING
        floor = PULLUP_FLOOR if exercise == 'pullup' else REP_FLOOR
        increment = FORMULAS[exercise]['increment']

        if failed:
            return current_weight, current_reps, True

        if current_reps >= ceiling:
            if exercise == 'pullup':
                return None, floor, False
            new_weight = current_weight + increment
            return round(new_weight * 2) / 2, floor, False
        else:
            return current_weight, current_reps + 1, False

    @staticmethod
    def apply_deload(exercise, current_weight, current_reps):
        floor = PULLUP_FLOOR if exercise == 'pullup' else REP_FLOOR
        if exercise == 'pullup':
            return None, floor
        deloaded = current_weight * DELOAD_FACTOR
        return round(deloaded * 2) / 2, floor