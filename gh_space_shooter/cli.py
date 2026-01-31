import argparse

from .github import fetch_contributions
from .utils import build_enemy_grid
from .models import Ship
from .engine import GameEngine
from .renderer import render_frame
from .gif import build_gif

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("username")
    parser.add_argument("-o", "--output", default="game.gif")
    parser.add_argument("--fps", type=int, default=40)
    parser.add_argument("--max-frames", type=int, default=200)

    args = parser.parse_args()

    print("Fetching GitHub data...")
    data = fetch_contributions(args.username)

    enemies = build_enemy_grid(data)
    ship = Ship()
    engine = GameEngine(enemies, ship)

    frames = []

    print("Simulating game...")
    for _ in range(args.max_frames):
        engine.step()
        frame = render_frame(engine.enemies, ship, engine.bullets)
        frames.append(frame)

        if not engine.enemies:
            break

    print("Building GIF...")
    build_gif(frames, args.output, args.fps)

    print(f"Done! Saved to {args.output}")
