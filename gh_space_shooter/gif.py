def build_gif(frames, output_path, fps=40):
    if not frames:
        raise ValueError("No frames to save")

    duration = int(1000 / fps)

    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=duration,
        loop=0,
        optimize=True
    )
