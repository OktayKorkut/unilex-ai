import re
import unicodedata


_TURKISH_FIXES = [
    (r'˙\s*I', 'İ'),
    (r'˙\s*i', 'i'),
    (r'¨\s*O', 'Ö'),
    (r'¨\s*o', 'ö'),
    (r'¨\s*U', 'Ü'),
    (r'¨\s*u', 'ü'),
    (r'¸\s*C', 'Ç'),
    (r'¸\s*c', 'ç'),
    (r'˘\s*G', 'Ğ'),
    (r'˘\s*g', 'ğ'),
    (r'¸\s*S', 'Ş'),
    (r'¸\s*s', 'ş'),
]


def fix_turkish_encoding(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    for pattern, replacement in _TURKISH_FIXES:
        text = re.sub(pattern, replacement, text)
    return text
