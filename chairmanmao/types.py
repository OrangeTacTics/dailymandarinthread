from __future__ import annotations
import typing as t
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


@dataclass
class Profile:
    username: str
    memberid: t.Optional[int]
    created: datetime

    last_message: datetime
    roles: t.List[Role]
    display_name: str

    credit: int
    hanzi: t.List[str]
    yuan: int


class Role(Enum):
    COMRADE = "Comrade"
    PARTY_MEMBER = "PartyMember"
    CHAIRMAN = "Chairman"
    LEARNER = "Learner"

    @staticmethod
    def from_str(role_name: str) -> Role:
        for role in Role:
            if role.value == role_name:
                return role
        raise ValueError(f'{role_name} is not a valid Role.')
