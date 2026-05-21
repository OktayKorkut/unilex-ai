import sys
try:
    from PIL import Image
except ImportError:
    pass

def recolor_logo_to_premium_gold(input_path, output_path):
    img = Image.open(input_path)
    img = img.convert("RGBA")
    datas = img.getdata()

    newData = []
    for item in datas:
        r, g, b, a = item
        if a > 50:
            # Detect dark navy colors (the book and cap)
            if r < 100 and g < 120 and b < 160:
                # Change to Premium Metallic Gold (212, 175, 55) which matches #d4af37
                newData.append((212, 175, 55, a))
            else:
                newData.append(item)
        else:
            newData.append(item)

    img.putdata(newData)
    img.save(output_path, "PNG")

print("Generating Premium Gold version to match buttons...")
recolor_logo_to_premium_gold("public/logo.png", "public/logo_gold.png")
print("Premium Gold logo created!")
