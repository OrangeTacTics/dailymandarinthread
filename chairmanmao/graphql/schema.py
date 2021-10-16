import typing as t
from datetime import datetime
from enum import Enum

import strawberry as s


@s.enum
class Role(Enum):
    party = "Party"
    learner = "Learner"


@s.type
class Profile:
  userId: str
  discord_username: str
  display_name: str
  credit: int
  hanzi: t.List[str]
  mined_words: t.List[str]
  roles: t.List[Role]
  created: datetime
  last_message: datetime
  yuan: int


@s.type
class Query:
    @s.field
    async def me(self, info) -> Profile:
        return await info.context.dataloaders.profile.load(876378479585808404)


schema = s.Schema(
    query=Query,
)
