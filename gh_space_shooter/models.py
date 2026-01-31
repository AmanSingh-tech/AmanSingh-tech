class Enemy:
    def __init__(self, x, y, hp):
        self.x = x
        self.y = y
        self.hp = hp
        self.alive = True


class Ship:
    def __init__(self, x=26, y=8):
        self.x = x
        self.y = y


class Bullet:
    def __init__(self, x, y):
        self.x = x
        self.y = y
