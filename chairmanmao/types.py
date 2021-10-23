from __future__ import annotations
import typing as t
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


@dataclass
class Profile:
    user_id: UserId

    discord_username: str
    display_name: str

    created: datetime
    last_seen: datetime

    roles: t.List[Role]

    credit: int
    yuan: int

    hanzi: t.List[str]
    mined_words: t.List[str]


class Role(Enum):
    Comrade = "Comrade"
    Party = "Party"
    Learner = "Learner"
    Jailed = "Jailed"
    Hsk1 = "Hsk1"
    Hsk2 = "Hsk2"
    Hsk3 = "Hsk3"
    Hsk4 = "Hsk4"
    Hsk5 = "Hsk5"
    Hsk6 = "Hsk6"

    @staticmethod
    def from_str(role_name: str) -> Role:
        for role in Role:
            if role.value == role_name:
                return role
        raise ValueError(f"{role_name} is not a valid Role.")

    def __lt__(self, other: object) -> bool:
        assert isinstance(other, Role)
        return self.value < other.value


@dataclass
class Exam:
    name: str
    deck: t.List[Question]
    num_questions: int
    max_wrong: t.Optional[int]
    timelimit: int
    hsk_level: int


@dataclass
class Question:
    question: str
    valid_answers: t.List[str]
    meaning: str

    def is_correct(self, answer: str) -> bool:
        return answer.lower() in self.valid_answers


UserId = int
Json = t.Any
