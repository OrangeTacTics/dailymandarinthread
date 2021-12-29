import typing as t

import strawberry as s

from .dictionary import DictEntry
from .exam import Exam, Question
from .profile import Profile, Role, get_me
from .admin import AdminQuery, AdminMutation


_ = Question, Role


@s.type
class Query:
    @s.field
    async def me(self, info) -> t.Optional[Profile]:
        return await get_me(info)

    @s.field
    async def profile(
        self,
        info,
        user_id: t.Optional[str] = None,
        discord_username: t.Optional[str] = None,
    ) -> t.Optional[Profile]:
        if user_id is not None:
            assert discord_username is None, "user_id and discord_username are mutually exclusive."
            return await info.context.dataloaders.profile.load(user_id)
        else:
            assert discord_username is not None, "One of user_id or discord_username must be provided."
            return await info.context.dataloaders.profile_by_discord_username.load(discord_username)

    @s.field
    async def leaderboard(self, info) -> t.List[Profile]:
        entries = []
        for profile in info.context.store.leaderboard():
            entries.append(await info.context.dataloaders.profile.load(str(profile.user_id)))
        return entries

    @s.field
    async def exam(self, info, name: str) -> t.Optional[Exam]:
        return await info.context.dataloaders.exam.load(name)

    @s.field
    async def exams(self, info) -> t.List[Exam]:
        return [info.context.dataloaders.exam.load(name) for name in info.context.store.get_exam_names()]

    @s.field
    def admin(self, info) -> AdminQuery:
        assert info.context.is_admin, "Must be admin"
        return AdminQuery()

    @s.field
    def dict(self, info, word: str) -> t.List[DictEntry]:
        results = []
        for store_dict_entry in info.context.store.dict_entry_lookup(word):
            results.append(
                DictEntry(
                    id=store_dict_entry.dict_entry_id,
                    simplified=store_dict_entry.simplified,
                    traditional=store_dict_entry.traditional,
                    pinyin_numbered=store_dict_entry.pinyin,
                    meanings=store_dict_entry.meanings,
                )
            )

        return results


@s.type
class Mutation:
    @s.field
    def admin(self, info) -> AdminMutation:
        assert info.context.is_admin, "Must be admin"
        return AdminMutation()

    @s.field
    async def set_name(self, info, name: str) -> Profile:
        assert len(name) < 32, "Name must be 32 characters or less."
        me = await get_me(info)
        with info.context.store.profile(int(me.user_id)) as profile:
            profile.display_name = name
            info.context.event_store.push(
                "NameChanged-1.0.0",
                {
                    "user_id": me.user_id,
                    "name": name,
                },
            )

        me.display_name = name
        return me


schema = s.Schema(
    query=Query,
    mutation=Mutation,
)
