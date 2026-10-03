TRIAGE_BASE = {"RED": 100, "YELLOW": 70, "GREEN": 40}

def calculate_priority(triage: str, waiting_minutes: int) -> int:
    triage = triage.upper()
    base = TRIAGE_BASE.get(triage, 40)
    if triage == "RED": aging = min(waiting_minutes, 5)
    elif triage == "YELLOW": aging = min(waiting_minutes // 2, 20)
    else: aging = min(waiting_minutes // 3, 20)
    return min(base + aging, 100)
