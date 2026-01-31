from .models import Bullet

class GameEngine:
    def __init__(self, enemies, ship):
        self.enemies = enemies
        self.ship = ship
        self.bullets = []

    def step(self):
        # Fire bullet every frame
        self.bullets.append(Bullet(self.ship.x, self.ship.y - 1))

        # Move bullets
        for bullet in self.bullets:
            bullet.y -= 1

        # Collision detection
        for enemy in self.enemies:
            for bullet in self.bullets:
                if enemy.x == bullet.x and enemy.y == bullet.y:
                    enemy.hp -= 1
                    bullet.y = -1
                    if enemy.hp <= 0:
                        enemy.alive = False

        # Cleanup
        self.enemies = [e for e in self.enemies if e.alive]
        self.bullets = [b for b in self.bullets if b.y >= 0]
