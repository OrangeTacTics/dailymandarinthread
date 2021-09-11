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


class Role(Enum):
    Comrade = "Comrade"
    Party = "Party"
    Learner = "Learner"
    Jailed = "Jailed"

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
