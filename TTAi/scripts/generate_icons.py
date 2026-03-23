import os, json
from PIL import Image, ImageDraw, ImageFont
root = r"C:\Users\vannt-pc\.openclaw\workspace\TTAi\Resources"
os.makedirs(root, exist_ok=True)
appicon_dir = os.path.join(root, 'AppIcon.appiconset')
os.makedirs(appicon_dir, exist_ok=True)
entries = [
    ('iphone', '20x20', '2x', 40, 'Icon-20@2x.png'),
    ('iphone', '20x20', '3x', 60, 'Icon-20@3x.png'),
    ('iphone', '29x29', '2x', 58, 'Icon-29@2x.png'),
    ('iphone', '29x29', '3x', 87, 'Icon-29@3x.png'),
    ('iphone', '40x40', '2x', 80, 'Icon-40@2x.png'),
    ('iphone', '40x40', '3x', 120, 'Icon-40@3x.png'),
    ('iphone', '60x60', '2x', 120, 'Icon-60@2x.png'),
    ('iphone', '60x60', '3x', 180, 'Icon-60@3x.png'),
    ('ipad', '20x20', '1x', 20, 'Icon-20-ipad.png'),
    ('ipad', '20x20', '2x', 40, 'Icon-20@2x-ipad.png'),
    ('ipad', '29x29', '1x', 29, 'Icon-29-ipad.png'),
    ('ipad', '29x29', '2x', 58, 'Icon-29@2x-ipad.png'),
    ('ipad', '40x40', '1x', 40, 'Icon-40-ipad.png'),
    ('ipad', '40x40', '2x', 80, 'Icon-40@2x-ipad.png'),
    ('ipad', '76x76', '1x', 76, 'Icon-76.png'),
    ('ipad', '76x76', '2x', 152, 'Icon-76@2x.png'),
    ('ipad', '83.5x83.5', '2x', 167, 'Icon-83.5@2x.png'),
    ('ios-marketing', '1024x1024', '1x', 1024, 'Icon-1024.png')
]
for idiom, size_label, scale, pixels, filename in entries:
    path = os.path.join(appicon_dir, filename)
    img = Image.new('RGBA', (pixels, pixels), (19, 30, 63, 255))
    draw = ImageDraw.Draw(img)
    for y in range(pixels):
        color = (int(25 + 80 * y / pixels), int(40 + 120 * y / pixels), int(120 + 80 * y / pixels), 255)
        draw.line([(0, y), (pixels, y)], fill=color)
    try:
        font_size = max(16, pixels // 3)
        font = ImageFont.truetype('arial.ttf', font_size)
    except Exception:
        font = ImageFont.load_default()
    text = 'TT'
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(((pixels - tw)/2, (pixels - th)/2), text, fill=(255, 255, 255, 255), font=font)
    img.save(path, format='PNG')
contents = {
    "images": [
        {
            "filename": filename,
            "idiom": idiom,
            "scale": scale,
            "size": size_label
        }
        for idiom, size_label, scale, pixels, filename in entries
    ],
    "info": {"version": 1, "author": "openclaw"}
}
with open(os.path.join(appicon_dir, 'Contents.json'), 'w', encoding='utf-8') as f:
    json.dump(contents, f, indent=2)
print('Icons generated at', appicon_dir)
