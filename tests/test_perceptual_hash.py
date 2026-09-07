from PIL import Image

from perceptual_hash import compute_phash, hamming_similarity


def test_identical_images_have_similarity_one(tmp_path):
    img = Image.new("RGB", (64, 64), color=(120, 40, 200))
    path_a, path_b = tmp_path / "a.png", tmp_path / "b.png"
    img.save(path_a)
    img.save(path_b)

    similarity = hamming_similarity(compute_phash(path_a), compute_phash(path_b))
    assert similarity == 1.0


def test_very_different_images_have_lower_similarity(tmp_path):
    img_a = Image.new("RGB", (64, 64), color=(0, 0, 0))
    img_b = Image.new("RGB", (64, 64), color=(255, 255, 255))
    path_a, path_b = tmp_path / "a.png", tmp_path / "b.png"
    img_a.save(path_a)
    img_b.save(path_b)

    similarity = hamming_similarity(compute_phash(path_a), compute_phash(path_b))
    assert similarity < 1.0
