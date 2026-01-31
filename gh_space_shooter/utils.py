from .models import Enemy

def build_enemy_grid(contrib_data):
    weeks = contrib_data["contributionCalendar"]["weeks"]
    enemies = []

    for x, week in enumerate(weeks):
        for y, day in enumerate(week["contributionDays"]):
            count = day["contributionCount"]
            if count > 0:
                enemies.append(
                    Enemy(x=x, y=y, hp=min(count, 5))
                )
    return enemies
