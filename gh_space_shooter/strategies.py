import random

def random_strategy(enemies):
    if not enemies:
        return None
    return random.choice(enemies)
