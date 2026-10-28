import io
import warnings
from dataclasses import dataclass
import numpy as np
from PIL import Image, ImageOps, ImageStat, UnidentifiedImageError
from app.core.errors import PublicError


@dataclass
class NormalizedImage:
    array: np.ndarray
    gemini_jpeg: bytes
    quality_warnings: list[str]
    width: int
    height: int


def normalize_image(data: bytes, settings) -> NormalizedImage:
    if not data:
        raise PublicError(422, "empty_image", "Choose a non-empty JPEG, PNG, or WebP image.")
    if len(data) > settings.max_upload_bytes:
        raise PublicError(413, "image_too_large", "Images must be at most 10 MiB.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as original:
                if original.format not in {"JPEG", "PNG", "WEBP"}:
                    raise PublicError(415, "unsupported_image_format", "Only JPEG, PNG, and WebP images are supported.")
                if getattr(original, "n_frames", 1) != 1:
                    raise PublicError(415, "animated_image", "Animated or multi-frame images are not supported.")
                width, height = original.size
                if width * height > settings.max_image_pixels or max(width, height) > settings.max_image_dimension:
                    raise PublicError(422, "image_dimensions_exceeded", "The decoded image is too large. Resize it before uploading.")
                if min(width, height) < 64:
                    raise PublicError(422, "poor_quality_image", "Use a clear image at least 64 pixels wide and high.")
                if original.mode not in {"RGB", "RGBA", "L", "LA", "P", "1", "CMYK"}:
                    raise PublicError(415, "unsupported_image_mode", "Convert the image to a standard RGB JPEG or PNG.")
                original.load()
                with ImageOps.exif_transpose(original) as oriented:
                    with oriented.convert("RGB") as rgb:
                        from ml.preprocessing import image_to_array
                        array = image_to_array(rgb)
                        rgb.thumbnail((1024, 1024), Image.Resampling.BILINEAR)
                        stats = ImageStat.Stat(rgb.resize((64, 64)))
                        quality_warnings = []
                        if max(stats.stddev) < 4:
                            quality_warnings.append("The image has very little visual detail; choose a clear, in-focus leaf photo.")
                        if max(stats.mean) < 18 or min(stats.mean) > 242:
                            quality_warnings.append("The image appears very dark or overexposed.")
                        output = io.BytesIO()
                        # No exif/icc metadata is copied to the new JPEG.
                        rgb.save(output, format="JPEG", quality=85, optimize=True)
                        return NormalizedImage(array, output.getvalue(), quality_warnings, width, height)
    except PublicError:
        raise
    except (Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise PublicError(422, "image_dimensions_exceeded", "The decoded image is too large. Resize it before uploading.")
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError):
        raise PublicError(422, "invalid_image", "The file is not a valid, complete JPEG, PNG, or WebP image.")
