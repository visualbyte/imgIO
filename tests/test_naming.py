"""Output naming and collision rules (PRD F4)."""

from __future__ import annotations

from imgio.core.naming import candidate_names, next_free_name, reserve_target


def test_candidates_start_plain_then_count():
    names = list(candidate_names("photo", ".jpg"))
    assert names[:4] == ["photo.jpg", "photo (1).jpg", "photo (2).jpg", "photo (3).jpg"]


def test_free_name_uses_source_name(tmp_path):
    assert next_free_name(tmp_path, "photo", ".jpg") == "photo.jpg"


def test_collision_increments(tmp_path):
    (tmp_path / "photo.jpg").write_bytes(b"x")
    assert next_free_name(tmp_path, "photo", ".jpg") == "photo (1).jpg"
    (tmp_path / "photo (1).jpg").write_bytes(b"x")
    assert next_free_name(tmp_path, "photo", ".jpg") == "photo (2).jpg"


def test_case_difference_counts_as_taken(tmp_path):
    (tmp_path / "Photo.JPG").write_bytes(b"x")
    assert next_free_name(tmp_path, "photo", ".jpg") == "photo (1).jpg"


def test_unicode_normalisation_counts_as_taken(tmp_path):
    composed = "caf\u00e9.jpg"      # é as one code point
    (tmp_path / composed).write_bytes(b"x")
    assert next_free_name(tmp_path, "cafe\u0301", ".jpg") == "cafe\u0301 (1).jpg"


def test_extension_is_always_lowercase(tmp_path):
    assert next_free_name(tmp_path, "photo", ".jpg").endswith(".jpg")


def test_reserve_creates_an_empty_file_and_never_reuses_a_name(tmp_path):
    source = tmp_path / "photo.png"
    source.write_bytes(b"png")

    first = reserve_target(source, ".jpg")
    second = reserve_target(source, ".jpg")

    assert first.name == "photo.jpg"
    assert second.name == "photo (1).jpg"
    assert first.exists() and second.exists()
    assert first.stat().st_size == 0


def test_reserve_keeps_the_source_casing(tmp_path):
    source = tmp_path / "Photo.png"
    source.write_bytes(b"png")
    assert reserve_target(source, ".jpg").name == "Photo.jpg"
