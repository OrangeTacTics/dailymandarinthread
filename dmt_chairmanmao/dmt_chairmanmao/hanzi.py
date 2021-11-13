from __future__ import annotations
import typing as t


def hanzis_in(text: str) -> t.List[str]:
    return [char for char in text if is_hanzi(char)]


def is_hanzi(char):
    """
    https://blog.ceshine.net/post/cjk-unicode/#respective-unicode-blocks
    """
    codepoint = ord(char)

    return (
        0x4E00 <= codepoint <= 0x9FFF
        or 0x3400 <= codepoint <= 0x4DBF
        or 0x20000 <= codepoint <= 0x2A6DF
        or 0x2A700 <= codepoint <= 0x2B73F
        or 0x2B740 <= codepoint <= 0x2B81F
        or 0x2B820 <= codepoint <= 0x2CEAF
        or 0xF900 <= codepoint <= 0xFAFF
        or 0x2F800 <= codepoint <= 0x2FA1F
    )
