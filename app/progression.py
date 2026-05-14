from datetime import date

FORMULAS = {
    'beginner': {
        'bench':    {'multiplier': 0.5, 'increment': 2.5},
        'squat':    {'multiplier': 0.75, 'increment': 10.0},
        'deadlift': {'multiplier': 0.65, 'increment': 5.0},
        'pullup':   {'multiplier': None, 'increment': None},
    },
    'intermediate': {
        'bench':    {'multiplier': 0.75, 'increment': 2.5},
        'squat':    {'multiplier': 1.0, 'increment': 10.0},
        'deadlift': {'multiplier': 0.8, 'increment': 5.0},
        'pullup':   {'multiplier': None, 'increment': 2.5},
    },
}

REP_FLOOR = 6
REP_CEILING = 12
PULLUP_FLOOR = 3
INTERMEDIATE_PULLUP_FLOOR = 8
PULLUP_CEILING = 10
SETS = 3
FAIL_THRESHOLD = 2
DELOAD_FACTOR = 0.75

class ProgressionEngine:

    @staticmethod
    def get_starting_weight(exercise, body_weight, experience='beginner'):
        experience = experience if experience in FORMULAS else 'beginner'
        if exercise == 'pullup':
            return 0.0 if experience == 'intermediate' else None
        multiplier = FORMULAS[experience][exercise]['multiplier']
        raw = body_weight * multiplier
        return round(raw * 2) / 2

    @staticmethod
    def get_starting_reps(exercise, experience='beginner'):
        experience = experience if experience in FORMULAS else 'beginner'
        if exercise == 'pullup' and experience == 'intermediate':
            return INTERMEDIATE_PULLUP_FLOOR
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
        weighted_pullup = exercise == 'pullup' and current_weight is not None
        ceiling = PULLUP_CEILING if exercise == 'pullup' else REP_CEILING
        floor = (
            INTERMEDIATE_PULLUP_FLOOR if weighted_pullup
            else PULLUP_FLOOR if exercise == 'pullup'
            else REP_FLOOR
        )
        increment = (
            FORMULAS['intermediate']['pullup']['increment'] if weighted_pullup
            else None if exercise == 'pullup'
            else FORMULAS['beginner'][exercise]['increment']
        )

        if failed:
            return current_weight, current_reps, True

        if current_reps >= ceiling:
            if exercise == 'pullup':
                if current_weight is None:
                    return None, floor, False
                new_weight = current_weight + increment
                return round(new_weight * 2) / 2, floor, False
            new_weight = current_weight + increment
            return round(new_weight * 2) / 2, floor, False
        else:
            return current_weight, current_reps + 1, False

    @staticmethod
    def apply_deload(exercise, current_weight, current_reps):
        weighted_pullup = exercise == 'pullup' and current_weight is not None
        floor = (
            INTERMEDIATE_PULLUP_FLOOR if weighted_pullup
            else PULLUP_FLOOR if exercise == 'pullup'
            else REP_FLOOR
        )
        if exercise == 'pullup':
            if current_weight is None:
                return None, floor
            deloaded = max(0, current_weight * DELOAD_FACTOR)
            return round(deloaded * 2) / 2, floor
        deloaded = current_weight * DELOAD_FACTOR
        return round(deloaded * 2) / 2, floor
