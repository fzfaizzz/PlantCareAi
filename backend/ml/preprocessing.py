"""Shared serving/training geometry. Model accepts float32 RGB in [0, 255]."""
INPUT_SIZE = (224, 224)
RESIZE_POLICY = 'bilinear_stretch'


def image_to_array(image):
    import numpy as np
    from PIL import Image, ImageOps
    oriented = ImageOps.exif_transpose(image)
    rgb = oriented.convert('RGB')
    resized = rgb.resize(INPUT_SIZE, Image.Resampling.BILINEAR)
    try:
        return np.array(resized, dtype=np.float32, copy=True)
    finally:
        resized.close()
        if rgb is not image:
            rgb.close()
        if oriented is not image:
            oriented.close()


def path_to_array(path):
    from PIL import Image
    with Image.open(path) as image:
        image.load()
        return image_to_array(image)
