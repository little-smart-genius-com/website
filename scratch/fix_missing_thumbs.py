import os
from PIL import Image

def center_crop_resize(img, target_w, target_h):
    w, h = img.size
    target_aspect = target_w / target_h
    current_aspect = w / h

    if current_aspect > target_aspect:
        # Image is too wide
        new_w = int(h * target_aspect)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))
    elif current_aspect < target_aspect:
        # Image is too tall
        new_h = int(w / target_aspect)
        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))

    return img.resize((target_w, target_h), Image.Resampling.LANCZOS)

def main():
    images_dir = "images"
    thumbs_dir = os.path.join(images_dir, "thumbs")
    os.makedirs(thumbs_dir, exist_ok=True)
    
    thumb_files = set(os.listdir(thumbs_dir))
    covers_without_thumbs = []
    
    for f in os.listdir(images_dir):
        if "-cover-" in f and f.endswith(".webp"):
            if f not in thumb_files:
                covers_without_thumbs.append(f)
                
    print(f"Found {len(covers_without_thumbs)} cover images missing thumbnails.")
    
    for i, cover in enumerate(covers_without_thumbs, 1):
        cover_path = os.path.join(images_dir, cover)
        thumb_path = os.path.join(thumbs_dir, cover)
        
        try:
            with Image.open(cover_path) as img:
                img = img.convert("RGB")
                thumb_img = center_crop_resize(img, 600, 338)
                thumb_img.save(thumb_path, "WEBP", quality=80, optimize=True)
            print(f"[{i}/{len(covers_without_thumbs)}] Generated thumbnail for {cover}")
        except Exception as e:
            print(f"[{i}/{len(covers_without_thumbs)}] Failed to generate thumb for {cover}: {e}")

if __name__ == "__main__":
    main()
