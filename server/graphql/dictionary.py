import typing as t

from dragonmapper.transcriptions import pinyin_to_zhuyin, numbered_syllable_to_accented
import strawberry as s


@s.type
class DictEntry:
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


def parse_dictentry(line: str) -> DictEntry:
    traditional, simplified, *_ = line.split(" ")
    left_brace = line.index("[")
    right_brace = line.index("]")
    pinyin_numbered = line[left_brace + 1 : right_brace]

    slash = line.index("/")
    meanings = []
    try:
        while True:
            line = line[slash + 1 :]
            slash = line.index("/")
            meaning = line[:slash]
            meanings.append(meaning)
    except:
        pass

    return DictEntry(
        simplified=simplified,
        traditional=traditional,
        pinyin_numbered=pinyin_numbered,
        meanings=meanings,
    )
