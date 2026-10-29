import os
import glob
from PIL import Image

def convert_all_frames():
    base_frames = r"D:\pitMOViE\XiaoQianPet\frames"
    out_dir = os.path.join(os.getcwd(), "frontend", "public", "assets", "pet_xiaoqian_webp")
    os.makedirs(out_dir, exist_ok=True)

    rows = sorted([d for d in os.listdir(base_frames) if os.path.isdir(os.path.join(base_frames, d))])
    for r in rows:
        frame_files = sorted(glob.glob(os.path.join(base_frames, r, "*.png")))
        if not frame_files:
            continue
        images = [Image.open(f).convert("RGBA") for f in frame_files]
        out_path = os.path.join(out_dir, f"{r}.webp")
        images[0].save(
            out_path,
            format="WEBP",
            save_all=True,
            append_images=images[1:],
            duration=120,
            loop=0,
            lossless=True,
            quality=100,
            method=4,
        )
        print(f"Converted {r}: {len(images)} frames -> {out_path}")

if __name__ == "__main__":
    convert_all_frames()
