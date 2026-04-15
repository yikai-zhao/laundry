"""
Generate realistic garment inspection sample photos.
Creates photos with realistic fabric textures, defects, and labels.
"""
import os, random, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = "/workspaces/laundry/demo/sample-photos"
os.makedirs(OUT, exist_ok=True)

W, H = 1200, 1600

def get_font(size):
    for path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def fabric_texture(img, base_color, variation=15):
    """Add realistic fabric texture."""
    draw = ImageDraw.Draw(img)
    w, h = img.size
    # Base fill
    img.paste(base_color, [0, 0, w, h])
    # Woven texture
    for y in range(0, h, 3):
        for x in range(0, w, 3):
            r = base_color[0] + random.randint(-variation, variation)
            g = base_color[1] + random.randint(-variation, variation)
            b = base_color[2] + random.randint(-variation, variation)
            r, g, b = max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))
            draw.point((x, y), fill=(r, g, b))
    # Slight blur for realism
    return img.filter(ImageFilter.GaussianBlur(radius=1))

def draw_garment_shape(img, garment_type, color):
    """Draw garment silhouette."""
    draw = ImageDraw.Draw(img)
    w, h = img.size
    
    if garment_type == "shirt":
        # Dress shirt silhouette
        points = [
            (w*0.25, h*0.12), (w*0.35, h*0.08), (w*0.45, h*0.06), (w*0.55, h*0.06),
            (w*0.65, h*0.08), (w*0.75, h*0.12),
            (w*0.85, h*0.18), (w*0.82, h*0.35), (w*0.7, h*0.30),
            (w*0.68, h*0.85), (w*0.32, h*0.85),
            (w*0.30, h*0.30), (w*0.18, h*0.35), (w*0.15, h*0.18),
        ]
        draw.polygon(points, fill=color, outline=(max(0, color[0]-40), max(0, color[1]-40), max(0, color[2]-40)))
        # Collar
        collar_color = tuple(min(255, c + 30) for c in color)
        draw.polygon([(w*0.38, h*0.08), (w*0.5, h*0.14), (w*0.62, h*0.08), (w*0.5, h*0.06)], fill=collar_color)
        # Buttons
        for i in range(6):
            by = h*0.15 + i * h*0.1
            draw.ellipse([w*0.48, by, w*0.52, by+12], fill=(200, 200, 200), outline=(150, 150, 150))
        # Pocket
        draw.rectangle([w*0.36, h*0.22, w*0.46, h*0.32], outline=(max(0, color[0]-30), max(0, color[1]-30), max(0, color[2]-30)), width=2)
        
    elif garment_type == "suit_jacket":
        points = [
            (w*0.2, h*0.12), (w*0.35, h*0.06), (w*0.5, h*0.05), (w*0.65, h*0.06), (w*0.8, h*0.12),
            (w*0.88, h*0.22), (w*0.84, h*0.38), (w*0.72, h*0.32),
            (w*0.72, h*0.88), (w*0.28, h*0.88),
            (w*0.28, h*0.32), (w*0.16, h*0.38), (w*0.12, h*0.22),
        ]
        draw.polygon(points, fill=color, outline=(max(0, color[0]-50), max(0, color[1]-50), max(0, color[2]-50)))
        # Lapels
        lapel_d = tuple(max(0, c - 25) for c in color)
        draw.polygon([(w*0.38, h*0.08), (w*0.5, h*0.28), (w*0.42, h*0.30), (w*0.34, h*0.10)], fill=lapel_d)
        draw.polygon([(w*0.62, h*0.08), (w*0.5, h*0.28), (w*0.58, h*0.30), (w*0.66, h*0.10)], fill=lapel_d)
        # Breast pocket
        draw.rectangle([w*0.55, h*0.22, w*0.66, h*0.28], outline=lapel_d, width=2)
        # Buttons
        for i in range(3):
            by = h*0.30 + i * h*0.12
            draw.ellipse([w*0.48, by, w*0.53, by+14], fill=(180, 170, 140), outline=(130, 120, 100))
            
    elif garment_type == "coat":
        points = [
            (w*0.18, h*0.10), (w*0.35, h*0.05), (w*0.5, h*0.04), (w*0.65, h*0.05), (w*0.82, h*0.10),
            (w*0.9, h*0.24), (w*0.86, h*0.42), (w*0.74, h*0.36),
            (w*0.74, h*0.92), (w*0.26, h*0.92),
            (w*0.26, h*0.36), (w*0.14, h*0.42), (w*0.1, h*0.24),
        ]
        draw.polygon(points, fill=color, outline=(max(0, color[0]-40), max(0, color[1]-40), max(0, color[2]-40)))
        # Belt
        belt_y = h * 0.55
        draw.rectangle([w*0.26, belt_y, w*0.74, belt_y+20], fill=(max(0, color[0]-60), max(0, color[1]-60), max(0, color[2]-60)))
        draw.ellipse([w*0.47, belt_y-2, w*0.53, belt_y+22], fill=(200, 180, 140))
        
    elif garment_type == "dress":
        # Top part
        points_top = [
            (w*0.3, h*0.10), (w*0.4, h*0.06), (w*0.6, h*0.06), (w*0.7, h*0.10),
            (w*0.78, h*0.18), (w*0.76, h*0.30), (w*0.68, h*0.26),
            (w*0.66, h*0.40), (w*0.34, h*0.40),
            (w*0.32, h*0.26), (w*0.24, h*0.30), (w*0.22, h*0.18),
        ]
        draw.polygon(points_top, fill=color, outline=(max(0, color[0]-30), max(0, color[1]-30), max(0, color[2]-30)))
        # Skirt (flared)
        for y_off in range(int(h*0.40), int(h*0.92)):
            flare = (y_off - h*0.40) / (h*0.52) * w*0.12
            x1 = w*0.34 - flare
            x2 = w*0.66 + flare
            shade = random.randint(-5, 5)
            line_color = tuple(max(0, min(255, c + shade)) for c in color)
            draw.line([(x1, y_off), (x2, y_off)], fill=line_color, width=1)

    elif garment_type == "pants":
        points = [
            (w*0.28, h*0.05), (w*0.72, h*0.05),
            (w*0.72, h*0.45), (w*0.62, h*0.45),
            (w*0.62, h*0.92), (w*0.52, h*0.92),
            (w*0.52, h*0.45), (w*0.48, h*0.45),
            (w*0.48, h*0.92), (w*0.38, h*0.92),
            (w*0.38, h*0.45), (w*0.28, h*0.45),
        ]
        draw.polygon(points, fill=color, outline=(max(0, color[0]-40), max(0, color[1]-40), max(0, color[2]-40)))
        # Waistband
        draw.rectangle([w*0.28, h*0.05, w*0.72, h*0.10], fill=tuple(max(0, c-20) for c in color))
    
    return img

def add_defect(img, defect_type, x_ratio, y_ratio, size_ratio=0.06):
    """Add a realistic defect at the specified position."""
    draw = ImageDraw.Draw(img)
    w, h = img.size
    cx, cy = int(x_ratio * w), int(y_ratio * h)
    s = int(size_ratio * min(w, h))
    
    if defect_type == "stain":
        # Irregular brown/dark stain shape
        for _ in range(200):
            dx = random.gauss(0, s*0.4)
            dy = random.gauss(0, s*0.3)
            px, py = int(cx + dx), int(cy + dy)
            if 0 <= px < w and 0 <= py < h:
                orig = img.getpixel((px, py))
                # Darken and brown-ify
                r = max(0, int(orig[0] * 0.5 + 30))
                g = max(0, int(orig[1] * 0.35 + 15))
                b = max(0, int(orig[2] * 0.25 + 5))
                draw.point((px, py), fill=(r, g, b))
        # edge blur
        region = img.crop((cx-s, cy-s, cx+s, cy+s))
        region = region.filter(ImageFilter.GaussianBlur(radius=2))
        img.paste(region, (cx-s, cy-s))
        
    elif defect_type == "tear":
        # Jagged tear line
        points = []
        for i in range(20):
            px = cx - s + i * (s*2 // 20) + random.randint(-3, 3)
            py = cy + random.randint(-s//3, s//3)
            points.append((px, py))
        draw.line(points, fill=(60, 50, 45), width=3)
        # Fraying threads
        for pt in points[::3]:
            for _ in range(4):
                ex = pt[0] + random.randint(-8, 8)
                ey = pt[1] + random.randint(-15, 15)
                draw.line([pt, (ex, ey)], fill=(120, 110, 100), width=1)
                
    elif defect_type == "missing_button":
        # Empty button hole with thread remnants
        draw.ellipse([cx-s//2, cy-s//2, cx+s//2, cy+s//2], outline=(100, 90, 80), width=2)
        # Thread remnants
        for _ in range(6):
            angle = random.random() * math.pi * 2
            ex = cx + int(math.cos(angle) * s * 0.3)
            ey = cy + int(math.sin(angle) * s * 0.3)
            draw.line([(cx, cy), (ex, ey)], fill=(180, 170, 160), width=1)
        # Button hole
        draw.line([(cx-s//4, cy), (cx+s//4, cy)], fill=(60, 55, 50), width=2)
                
    elif defect_type == "wear":
        # Fabric thinning / pilling area
        for _ in range(300):
            dx = random.gauss(0, s*0.5)
            dy = random.gauss(0, s*0.5)
            px, py = int(cx + dx), int(cy + dy)
            if 0 <= px < w and 0 <= py < h:
                orig = img.getpixel((px, py))
                # Lighten (worn look)
                r = min(255, int(orig[0] * 1.2 + 20))
                g = min(255, int(orig[1] * 1.2 + 20))
                b = min(255, int(orig[2] * 1.2 + 20))
                draw.point((px, py), fill=(r, g, b))
    
    elif defect_type == "hole":
        # Dark hole with frayed edges
        draw.ellipse([cx-s//2, cy-s//3, cx+s//2, cy+s//3], fill=(30, 25, 20))
        # Frayed edges
        for angle in range(0, 360, 15):
            rad = math.radians(angle)
            ex = cx + int(math.cos(rad) * (s//2 + random.randint(2, 8)))
            ey = cy + int(math.sin(rad) * (s//3 + random.randint(2, 6)))
            sx = cx + int(math.cos(rad) * s//2 * 0.8)
            sy = cy + int(math.sin(rad) * s//3 * 0.8)
            draw.line([(sx, sy), (ex, ey)], fill=(80, 70, 60), width=1)

    return img

def add_background(img):
    """Add inspection table background."""
    draw = ImageDraw.Draw(img)
    w, h = img.size
    # Light grey table surface
    for y in range(h):
        for x in range(0, w, 8):
            v = 230 + random.randint(-8, 8)
            draw.rectangle([x, y, x+8, y+1], fill=(v, v, v))
    return img

# ── Generate garment photos ──

garments = [
    {
        "name": "white_shirt",
        "type": "shirt",
        "color": (235, 235, 230),
        "defects": [
            ("stain", 0.42, 0.25, 0.05),  # Coffee stain on front chest
            ("missing_button", 0.50, 0.55, 0.025),  # Third button missing
        ]
    },
    {
        "name": "navy_suit",
        "type": "suit_jacket",
        "color": (35, 45, 70),
        "defects": [
            ("wear", 0.35, 0.80, 0.08),  # Elbow wear
            ("stain", 0.60, 0.35, 0.04),  # Small grease stain on lapel
        ]
    },
    {
        "name": "beige_coat",
        "type": "coat",
        "color": (195, 175, 150),
        "defects": [
            ("tear", 0.65, 0.70, 0.07),  # Tear near pocket
            ("stain", 0.40, 0.60, 0.06),  # Large stain on front
        ]
    },
    {
        "name": "red_dress",
        "type": "dress",
        "color": (165, 35, 45),
        "defects": [
            ("stain", 0.55, 0.65, 0.04),  # Wine stain on skirt
        ]
    },
    {
        "name": "grey_pants",
        "type": "pants",
        "color": (110, 110, 115),
        "defects": [
            ("wear", 0.45, 0.40, 0.06),  # Wear at knee area
            ("hole", 0.50, 0.75, 0.03),  # Small hole near hem
        ]
    },
]

for g in garments:
    for view in ["front", "back"]:
        img = Image.new("RGB", (W, H), (230, 230, 230))
        img = add_background(img)
        
        color = g["color"]
        if view == "back":
            # Slightly different shade for back
            color = tuple(max(0, min(255, c - 8)) for c in color)
        
        img = draw_garment_shape(img, g["type"], color)
        
        # Add defects only to front view
        if view == "front":
            for defect in g["defects"]:
                img = add_defect(img, defect[0], defect[1], defect[2], defect[3])
        
        # Add subtle label
        font_small = get_font(18)
        draw = ImageDraw.Draw(img)
        label_text = f'{g["name"].replace("_", " ").title()} - {view.upper()}'
        draw.text((20, H - 40), label_text, fill=(180, 180, 180), font=font_small)
        
        filename = f'{g["name"]}_{view}.jpg'
        img.save(os.path.join(OUT, filename), "JPEG", quality=92)
        print(f"  Created: {filename}")

print(f"\n✅ Generated {len(garments) * 2} sample photos in {OUT}")
