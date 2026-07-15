import os
import random
import numpy as np
from PIL import Image, ImageDraw, ImageChops
import pypdfium2 as pdfium

def apply_scan_effects(pil_image, page_idx):
    # Convert to RGB if not already
    if pil_image.mode != "RGB":
        pil_image = pil_image.convert("RGB")
        
    width, height = pil_image.size
    
    # 1. Page Skew/Rotation
    # Use small alternating angles for realism (-0.9 to +0.9 degrees)
    angle = -0.7 if page_idx % 2 == 0 else 0.8
    # Rotate with white background fill
    rotated = pil_image.rotate(angle, resample=Image.BICUBIC, expand=True, fillcolor=(255, 255, 255))
    rot_w, rot_h = rotated.size
    
    # 2. Scanner Shadow Gradient
    # We will simulate a shadow on the left edge (lid curvature/binding shadow)
    # create a linear gradient image
    gradient = Image.new("L", (rot_w, rot_h), 255)
    draw = ImageDraw.Draw(gradient)
    shadow_width = int(rot_w * 0.08) # 8% of width
    
    # Left edge shadow gradient: starts at 180 (darker) and goes to 255 (white)
    for x in range(shadow_width):
        brightness = int(185 + (255 - 185) * (x / shadow_width))
        draw.line([(x, 0), (x, rot_h)], fill=brightness)
        
    # Top edge shadow gradient (minor)
    shadow_height = int(rot_h * 0.02)
    for y in range(shadow_height):
        brightness = int(210 + (255 - 210) * (y / shadow_height))
        # Draw with blending to not override the left edge shadow entirely
        # We overlay linear transparency
        existing_val = gradient.getpixel((0, y)) if hasattr(gradient, 'getpixel') else 255
        # fallback simple math
        draw.line([(0, y), (rot_w, y)], fill=min(brightness, 230))

    # Combine shadow with the image
    gradient_rgb = Image.merge("RGB", (gradient, gradient, gradient))
    shadowed = ImageChops.multiply(rotated, gradient_rgb)
    
    # 3. Grayscale conversion
    grayscaled = shadowed.convert("L")
    
    # 4. Light photocopy scan noise
    arr = np.array(grayscaled)
    # Generate Gaussian noise (mean=0, std=4.5)
    noise = np.random.normal(0, 4.5, arr.shape)
    # Clip values to [0, 255]
    noisy_arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    
    # Apply a tiny blur/threshold to simulate ink bleed/xerox contrast
    noisy_img = Image.fromarray(noisy_arr)
    
    return noisy_img

def generate_scanned_timetable():
    clean_pdf_path = "timetable_clean.pdf"
    if not os.path.exists(clean_pdf_path):
        print(f"Error: {clean_pdf_path} not found. Please run generate_pdf.py first.")
        return
        
    print("Loading timetable_clean.pdf...")
    doc = pdfium.PdfDocument(clean_pdf_path)
    scanned_images = []
    
    for i in range(len(doc)):
        print(f"Processing page {i+1}/{len(doc)}...")
        page = doc[i]
        # Render page at 300 DPI (approx scale=4)
        bitmap = page.render(scale=4)
        pil_img = bitmap.to_pil()
        
        # Apply scanned photocopy effects
        scanned_img = apply_scan_effects(pil_img, i)
        scanned_images.append(scanned_img)
        
    # Save compilation back into a single PDF
    if scanned_images:
        output_path = "timetable_scanned.pdf"
        scanned_images[0].save(
            output_path, 
            save_all=True, 
            append_images=scanned_images[1:], 
            resolution=300
        )
        print(f"{output_path} generated successfully with scanned effects.")

if __name__ == "__main__":
    generate_scanned_timetable()
