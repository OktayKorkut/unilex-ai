import sys
try:
    from PIL import Image
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image

def recolor_logo_for_dark_mode(input_path, output_path):
    img = Image.open(input_path)
    img = img.convert("RGBA")
    datas = img.getdata()

    newData = []
    for item in datas:
        r, g, b, a = item
        # If it's a visible pixel
        if a > 50:
            # Detect dark navy colors (the book and cap)
            if r < 100 and g < 120 and b < 160:
                # Change dark navy to pure White for dark mode contrast
                newData.append((255, 255, 255, a))
            else:
                # Keep the cyan circuit tree as is
                newData.append(item)
        else:
            newData.append(item)

    img.putdata(newData)
    img.save(output_path, "PNG")

print("Processing logo to make it pop in dark mode...")
recolor_logo_for_dark_mode("public/logo.png", "public/logo_light.png")
print("Logo recolored to logo_light.png!")
