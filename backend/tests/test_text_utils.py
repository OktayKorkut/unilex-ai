import pytest

from app.core.text_utils import fix_turkish_encoding


@pytest.mark.parametrize(
    "broken, expected",
    [
        ("˙Istanbul", "İstanbul"),
        ("˙ib", "ib"),
        ("¨Ogrenci", "Ögrenci"),
        ("¨ogrenci", "ögrenci"),
        ("¨Universite", "Üniversite"),
        ("¨universite", "üniversite"),
        ("¸Cal¸sma", "Çalşma"),
        ("a¸cık", "açık"),
        ("˘Gaye", "Ğaye"),
        ("do˘gru", "doğru"),
        ("¸Subat", "Şubat"),
        ("ba¸svuru", "başvuru"),
    ],
)
def test_broken_pdf_accents_are_repaired(broken, expected):
    assert fix_turkish_encoding(broken) == expected


def test_whitespace_between_accent_and_letter_is_tolerated():
    assert fix_turkish_encoding("¨ O") == "Ö"


def test_decomposed_unicode_is_normalized():
    # "u" + birleştirici ¨ işareti, tek karakterli "ü" olmalı
    assert fix_turkish_encoding("ü") == "ü"


def test_clean_text_is_unchanged():
    text = "Çift anadal başvurusu için GNO şartı nedir? İğdır, Öğretim, Üniversite."
    assert fix_turkish_encoding(text) == text


def test_fix_is_idempotent():
    once = fix_turkish_encoding("¨universite ba¸svuru do˘gru")
    assert fix_turkish_encoding(once) == once
