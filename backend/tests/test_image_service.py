import io
import pytest
from PIL import Image
from conftest import image_bytes
from app.core.errors import PublicError
from app.services.image_service import normalize_image


@pytest.mark.parametrize("fmt", ["JPEG", "PNG", "WEBP"])
def test_supported_decode_and_preprocessing(settings, fmt):
    result = normalize_image(image_bytes(fmt), settings)
    assert result.array.shape == (224, 224, 3)
    assert result.array.min() >= 0 and result.array.max() <= 255
    with Image.open(io.BytesIO(result.gemini_jpeg)) as image:
        assert image.mode == "RGB"
        assert not image.getexif()


def test_pixel_limit_before_loading(settings):
    settings.max_image_pixels = 4096
    with pytest.raises(PublicError) as error:
        normalize_image(image_bytes(size=(128, 128)), settings)
    assert error.value.code == "image_dimensions_exceeded"


def test_decompression_bomb(settings, monkeypatch):
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 100)
    with pytest.raises(PublicError) as error:
        normalize_image(image_bytes(), settings)
    assert error.value.code == "image_dimensions_exceeded"


def test_animation_rejected(settings):
    output = io.BytesIO()
    Image.new("RGB", (80, 80), "green").save(output, "WEBP", save_all=True,
                                           append_images=[Image.new("RGB", (80, 80), "red")], duration=100, loop=0)
    with pytest.raises(PublicError) as error:
        normalize_image(output.getvalue(), settings)
    assert error.value.code == "animated_image"


def test_other_image_formats_rejected(settings):
    output = io.BytesIO()
    Image.new("RGB", (80, 80)).save(output, "BMP")
    with pytest.raises(PublicError) as error:
        normalize_image(output.getvalue(), settings)
    assert error.value.code == "unsupported_image_format"


def test_flat_image_quality_warning(settings):
    output = io.BytesIO()
    Image.new("RGB", (80, 80), "green").save(output, "PNG")
    assert normalize_image(output.getvalue(), settings).quality_warnings


def test_exif_orientation_and_strip(settings):
    output = io.BytesIO()
    image = Image.new("RGB", (80, 120), "green")
    exif = Image.Exif()
    exif[274] = 6
    exif[270] = "secret test text"
    image.save(output, "JPEG", exif=exif)
    result = normalize_image(output.getvalue(), settings)
    with Image.open(io.BytesIO(result.gemini_jpeg)) as clean:
        assert clean.size == (120, 80)
        assert len(clean.getexif()) == 0
