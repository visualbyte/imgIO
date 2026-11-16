"""Conversion behaviour (PRD F3 to F8, F12, F13)."""

from __future__ import annotations

import pytest
from PIL import Image

from imgio.core import decoders
from imgio.core.convert import Format, Status, convert

decoders.register()


def make_image(path, size=(40, 30), mode="RGB", colour=(200, 30, 30), **save):
    image = Image.new(mode, size, colour)
    image.save(path, **save)
    image.close()
    return path


def test_png_becomes_jpg_beside_the_source(tmp_path):
    source = make_image(tmp_path / "photo.png")
    original = source.read_bytes()

    result = convert(source, Format.JPG, 90)

    assert result.status is Status.CONVERTED
    assert result.output == tmp_path / "photo.jpg"
    assert result.output.exists()
    assert source.read_bytes() == original
    assert Image.open(result.output).format == "JPEG"


def test_file_already_in_target_format_is_re_encoded_and_suffixed(tmp_path):
    source = make_image(tmp_path / "photo.jpg", format="JPEG", quality=95)

    result = convert(source, Format.JPG, 40)

    assert result.status is Status.CONVERTED
    assert result.output == tmp_path / "photo (1).jpg"
    assert result.output_bytes < result.source_bytes


def test_existing_target_is_never_overwritten(tmp_path):
    make_image(tmp_path / "photo.jpg", colour=(0, 0, 255))
    before = (tmp_path / "photo.jpg").read_bytes()
    source = make_image(tmp_path / "photo.png")

    result = convert(source, Format.JPG, 90)

    assert result.output == tmp_path / "photo (1).jpg"
    assert (tmp_path / "photo.jpg").read_bytes() == before


def test_transparency_is_flattened_onto_white(tmp_path):
    source = tmp_path / "logo.png"
    image = Image.new("RGBA", (20, 20), (255, 0, 0, 0))
    image.save(source)
    image.close()

    result = convert(source, Format.JPG, 95)

    pixel = Image.open(result.output).convert("RGB").getpixel((10, 10))
    assert all(channel > 240 for channel in pixel)


def test_png_output_keeps_transparency(tmp_path):
    source = tmp_path / "logo.png"
    image = Image.new("RGBA", (20, 20), (255, 0, 0, 0))
    image.save(source)
    image.close()

    result = convert(source, Format.PNG, 90)

    assert result.status is Status.CONVERTED
    assert result.output == tmp_path / "logo (1).png"
    assert Image.open(result.output).mode == "RGBA"


def test_exif_rotation_is_applied_once(tmp_path):
    source = tmp_path / "portrait.jpg"
    image = Image.new("RGB", (20, 10), (10, 10, 10))
    exif = Image.Exif()
    exif[0x0112] = 6  # rotate 90 degrees clockwise
    image.save(source, exif=exif)
    image.close()

    result = convert(source, Format.JPG, 90)

    output = Image.open(result.output)
    assert output.size == (10, 20)
    # The tag must be gone, or a second viewer would rotate the upright image again.
    assert 0x0112 not in output.getexif()


def test_icc_profile_is_kept(tmp_path):
    from PIL import ImageCms

    profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    source = tmp_path / "wide.jpg"
    Image.new("RGB", (16, 16), (1, 2, 3)).save(source, icc_profile=profile)

    result = convert(source, Format.JPG, 90)

    assert Image.open(result.output).info.get("icc_profile") == profile


def test_unsupported_file_is_skipped(tmp_path):
    source = tmp_path / "notes.txt"
    source.write_text("not an image")

    result = convert(source, Format.JPG, 90)

    assert result.status is Status.SKIPPED
    assert "supported" in result.message.lower()


def test_corrupt_image_is_reported_not_raised(tmp_path):
    source = tmp_path / "broken.png"
    source.write_bytes(b"\x89PNG\r\n\x1a\n" + b"garbage")

    result = convert(source, Format.JPG, 90)

    assert result.status is Status.FAILED
    assert result.output is None


def test_zero_byte_file_is_reported(tmp_path):
    source = tmp_path / "empty.jpg"
    source.write_bytes(b"")

    result = convert(source, Format.JPG, 90)

    assert result.status is Status.FAILED


def test_error_messages_never_show_an_empty_reason(tmp_path):
    source = tmp_path / "broken.png"
    source.write_bytes(b"\x89PNG\r\n\x1a\n" + b"junk")
    result = convert(source, Format.JPG, 90)
    assert "none" not in result.message.lower()
    assert result.message == "File could not be read"


def test_16_bit_png_is_written_as_8_bit(tmp_path):
    source = tmp_path / "deep.png"
    image = Image.new("I;16", (10, 10), 30000)
    image.save(source)
    image.close()

    result = convert(source, Format.PNG, 90)

    assert result.status is Status.CONVERTED
    assert Image.open(result.output).mode in ("L", "RGB", "RGBA")


def test_cmyk_jpeg_becomes_rgb_jpeg(tmp_path):
    source = tmp_path / "print.jpg"
    image = Image.new("CMYK", (20, 20), (0, 100, 100, 0))
    image.save(source, format="JPEG")
    image.close()

    result = convert(source, Format.JPG, 90)

    assert result.status is Status.CONVERTED
    assert Image.open(result.output).mode == "RGB"


def test_animated_gif_converts_the_first_frame(tmp_path):
    first = Image.new("RGB", (10, 10), (255, 0, 0))
    second = Image.new("RGB", (10, 10), (0, 0, 255))
    source = tmp_path / "anim.gif"
    first.save(source, save_all=True, append_images=[second], duration=100, loop=0)
    first.close()
    second.close()

    result = convert(source, Format.JPG, 90)

    assert result.status is Status.CONVERTED
    assert "first frame" in " ".join(result.notes).lower()


def test_lower_quality_makes_a_smaller_file(tmp_path):
    source = tmp_path / "detail.png"
    image = Image.new("RGB", (400, 400))
    pixels = image.load()
    for y in range(400):
        for x in range(400):
            pixels[x, y] = ((x * 7) % 256, (y * 5) % 256, ((x + y) * 3) % 256)
    image.save(source)
    image.close()

    high = convert(source, Format.JPG, 95)
    low_source = tmp_path / "detail2.png"
    source.replace(low_source)
    low = convert(low_source, Format.JPG, 20)

    assert low.output_bytes < high.output_bytes


def test_heic_becomes_jpg(tmp_path):
    pytest.importorskip("pillow_heif")
    if decoders.heif_unavailable_reason():
        pytest.skip(decoders.heif_unavailable_reason())

    source = tmp_path / "IMG_0001.heic"
    image = Image.new("RGB", (32, 24), (30, 120, 200))
    image.save(source, format="HEIF")
    image.close()

    result = convert(source, Format.JPG, 90)

    assert result.status is Status.CONVERTED
    assert result.output == tmp_path / "IMG_0001.jpg"
