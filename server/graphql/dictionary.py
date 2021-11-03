import typing as t

from dragonmapper.transcriptions import pinyin_to_zhuyin, numbered_syllable_to_accented
import strawberry as s


@s.type
class DictEntry:
    id: s.ID
    simplified: str
    traditional: str
    pinyin_numbered: str
    meanings: t.List[str]

    @s.field
    def pinyin(self) -> str:
        pinyin = " ".join(numbered_syllable_to_accented(s) for s in self.pinyin_numbered.split(" "))
        return pinyin

    @s.field
    def zhuyin(self) -> str:
        zhuyin = pinyin_to_zhuyin(self.pinyin_numbered)
        return zhuyin
