"""The screenshots script only rewrites a capture whose pixels changed (not its PNG bytes)."""

import importlib.util
import io
from pathlib import Path

from PIL import Image

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "screenshots.py"


def _script():
    spec = importlib.util.spec_from_file_location("hr_screenshots", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _png(color, size=(4, 3), level=6):
    buf = io.BytesIO()
    Image.new("RGBA", size, color).save(buf, "PNG", compress_level=level)
    return buf.getvalue()


def test_same_pixels_ignores_the_png_encoding():
    same_pixels = _script().same_pixels
    a, b = _png((10, 20, 30, 255), level=1), _png((10, 20, 30, 255), level=9)
    assert a != b  # other bytes (zlib level)...
    assert same_pixels(a, b)  # ...same picture: the file is kept


def test_same_pixels_sees_a_change():
    same_pixels = _script().same_pixels
    assert not same_pixels(_png((10, 20, 30, 255)), _png((10, 20, 31, 255)))
    assert not same_pixels(_png((10, 20, 30, 255)), _png((10, 20, 30, 255), size=(4, 4)))
    assert not same_pixels(b"not a png", _png((10, 20, 30, 255)))
