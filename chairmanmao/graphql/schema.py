import typing as t
from datetime import datetime
from enum import Enum

import strawberry as s


@s.enum
class Role(Enum):
    Party = "Party"
    Learner = "Learner"
    Jailed = "Jailed"


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
  last_seen: datetime
  yuan: int


@s.type
class Query:
    @s.field
    async def me(self, info) -> t.Optional[Profile]:
        discord_username = info.context.discord_username
        return await info.context.dataloaders.profile_by_discord_username.load(discord_username)

    @s.field
    async def profile(
        self,
        info,
        user_id: t.Optional[str] = None,
        discord_username: t.Optional[str] = None,
    ) -> t.Optional[Profile]:
        if user_id is not None:
            assert discord_username is None, 'user_id and discord_username are mutually exclusive.'
            return await info.context.dataloaders.profile.load(user_id)
        else:
            assert discord_username is not None, 'One of user_id or discord_username must be provided.'
            return await info.context.dataloaders.profile_by_discord_username.load(discord_username)


@s.type
class Mutation:
    @s.field
    async def jail(self, info, user_id: str) -> Profile:
        assert info.context.is_admin, 'Must be admin'
        info.context.api.jail(int(user_id))
        return await info.context.dataloaders.profile.load(user_id)

    @s.field
    async def unjail(self, info, user_id: str) -> Profile:
        assert info.context.is_admin, 'Must be admin'
        info.context.api.unjail(int(user_id))
        return await info.context.dataloaders.profile.load(user_id)


schema = s.Schema(
    query=Query,
    mutation=Mutation,
)
