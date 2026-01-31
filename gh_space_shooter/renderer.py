from PIL import Image, ImageDraw

CELL = 14
WIDTH = 52
HEIGHT = 10

def render_frame(enemies, ship, bullets):
    img = Image.new(
        "RGB",
        (WIDTH * CELL, HEIGHT * CELL),
        "black"
    )
    draw = ImageDraw.Draw(img)

    # Enemies
    for e in enemies:
        draw.rectangle(
            [e.x*CELL, e.y*CELL, e.x*CELL+10, e.y*CELL+10],
            fill="green"
        )

    # Ship
    draw.rectangle(
        [ship.x*CELL, ship.y*CELL, ship.x*CELL+10, ship.y*CELL+10],
        fill="white"
    )

    # Bullets
    for b in bullets:
        draw.rectangle(
            [b.x*CELL+4, b.y*CELL, b.x*CELL+6, b.y*CELL+6],
            fill="red"
        )

    return img
