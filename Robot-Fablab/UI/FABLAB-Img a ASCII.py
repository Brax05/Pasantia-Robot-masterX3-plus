from PIL import Image

# Caracteres ASCII ordenados de más oscuro a más claro
ASCII_CHARS = "@%#*+=-:. "

def pixels_to_ascii(image):
    pixels = list(image.getdata())  # evita warning futuro
    ascii_str = ""

    for pixel in pixels:
        ascii_str += ASCII_CHARS[pixel * len(ASCII_CHARS) // 256]

    return ascii_str

def resize_image(image, new_width=100):
    width, height = image.size
    aspect_ratio = height / width
    new_height = int(aspect_ratio * new_width * 0.55)
    return image.resize((new_width, new_height))

def grayscale(image):
    return image.convert("L")

def image_to_ascii(path, width=100):
    image = Image.open(path)
    image = resize_image(image, width)
    image = grayscale(image)

    ascii_str = pixels_to_ascii(image)

    img_width = image.width
    ascii_img = ""
    for i in range(0, len(ascii_str), img_width):
        ascii_img += ascii_str[i:i+img_width] + "\n"

    return ascii_img

# Uso
ruta_imagen = "C:/Users/bprado/Downloads/ola.jpg"
ascii_art = image_to_ascii(ruta_imagen, width=120)

print(ascii_art)

# Guardar en archivo
with open("ascii.txt", "w") as f:
    f.write(ascii_art)