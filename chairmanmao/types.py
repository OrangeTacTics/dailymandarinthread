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

    def is_jailed(self) -> bool:
        return Role.Jailed in self.roles

    def is_party(self) -> bool:
        return Role.Party in self.roles

    def is_learner(self) -> bool:
        return Role.Learner in self.roles

    def hsk_level(self) -> t.Optional[int]:
        if Role.Hsk1 in self.roles:
            return 1
        elif Role.Hsk2 in self.roles:
            return 2
        elif Role.Hsk3 in self.roles:
            return 3
        elif Role.Hsk4 in self.roles:
            return 4
        elif Role.Hsk5 in self.roles:
            return 5
        elif Role.Hsk6 in self.roles:
            return 6
        else:
            return None

    def hsk_role(self) -> t.Optional[Role]:
        if Role.Hsk1 in self.roles:
            return Role.Hsk1
        elif Role.Hsk2 in self.roles:
            return Role.Hsk2
        elif Role.Hsk3 in self.roles:
            return Role.Hsk3
        elif Role.Hsk4 in self.roles:
            return Role.Hsk4
        elif Role.Hsk5 in self.roles:
            return Role.Hsk5
        elif Role.Hsk6 in self.roles:
            return Role.Hsk6
        else:
            return None


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
        raise ValueError(f'{role_name} is not a valid Role.')

    def __lt__(self, other: object) -> bool:
        assert isinstance(other, Role)
        return self.value < other.value


UserId = int
Json = t.Any
