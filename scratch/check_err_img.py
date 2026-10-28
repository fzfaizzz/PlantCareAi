from PIL import Image

im = Image.open("qa/browser-error.png")
print("Image size:", im.size)
print("Mode:", im.mode)
