import typing as t
from datetime import datetime, timezone

import strawberry as s

from .exam import Exam, ExamMutation, NewExam
from .profile import Profile, add_role, remove_role, set_hsk
from .server_settings import ServerSettings
import server.store.types as types


@s.type
class AdminQuery:
    @s.field
    async def all_profiles(self, info) -> t.List[Profile]:
        assert info.context.is_admin, "Must be admin"

        profiles = []
        for profile in info.context.store.get_all_profiles():
            profiles.append(await info.context.dataloaders.profile.load(str(profile.user_id)))
        return profiles

    @s.field
    async def server_settings(self, info) -> ServerSettings:
        server_settings = info.context.store.load_server_settings()
        return ServerSettings(last_bump=server_settings.last_bump)


@s.type
class AdminMutation:
    @s.field
    async def register(self, info, user_id: str, discord_username: str) -> Profile:
        assert info.context.is_admin, "Must be admin"
        info.context.store.create_profile(int(user_id), discord_username)
        return await info.context.dataloaders.profile.load(user_id)

    @s.field
    async def alert_activity(self, info, user_ids: t.List[str]) -> datetime:
        now = datetime.now(timezone.utc).replace(microsecond=0)
        for user_id in user_ids:
            with info.context.store.profile(int(user_id)) as profile:
                profile.last_seen = now

        return now

    @s.field
    async def honor(self, info, user_id: str, amount: int) -> Profile:
        assert amount > 0

        with info.context.store.profile(int(user_id)) as profile:
            profile.credit += amount

        return await info.context.dataloaders.profile.load(user_id)

    @s.field
    async def dishonor(self, info, user_id: str, amount: int) -> Profile:
        assert amount > 0

        with info.context.store.profile(int(user_id)) as profile:
            profile.credit -= amount

        return await info.context.dataloaders.profile.load(user_id)

    @s.field
    async def transfer(self, info, from_user_id: str, to_user_id: str, amount: int) -> bool:
        assert amount > 0

        with info.context.store.profile(int(from_user_id)) as from_profile:
            assert amount <= from_profile.yuan, "Insufficient funds"
            from_profile.yuan -= amount

        with info.context.store.profile(int(to_user_id)) as to_profile:
            to_profile.yuan += amount

        return True

    @s.field
    async def jail(self, info, user_id: str) -> Profile:
        with info.context.store.profile(int(user_id)) as profile:
            if not add_role(profile, types.Role.Jailed):
                raise Exception("Already jailed")

        return await info.context.dataloaders.profile.load(user_id)

    @s.field
    async def unjail(self, info, user_id: str) -> Profile:
        with info.context.store.profile(int(user_id)) as profile:
            if not remove_role(profile, types.Role.Jailed):
                raise Exception("Not jailed")

        return await info.context.dataloaders.profile.load(user_id)

    @s.field
    async def set_name(self, info, user_id: str, name: str) -> Profile:
        assert len(name) < 32, "Name must be 32 characters or less."
        with info.context.store.profile(int(user_id)) as profile:
            profile.display_name = name

        return await info.context.dataloaders.profile.load(user_id)

    @s.field
    async def set_hsk(self, info, user_id: str, hsk: t.Optional[int]) -> Profile:
        with info.context.store.profile(int(user_id)) as profile:
            set_hsk(profile, hsk)

        return await info.context.dataloaders.profile.load(user_id)

    @s.field
    async def set_party(self, info, user_id: str, flag: bool = True) -> Profile:
        with info.context.store.profile(int(user_id)) as profile:
            if flag:
                add_role(profile, types.Role.Party)
            else:
                remove_role(profile, types.Role.Party)

        return await info.context.dataloaders.profile.load(user_id)

    @s.field
    async def set_learner(self, info, user_id: str, flag: bool = True) -> Profile:
        with info.context.store.profile(int(user_id)) as profile:
            if flag:
                add_role(profile, types.Role.Learner)
            else:
                remove_role(profile, types.Role.Learner)

        return await info.context.dataloaders.profile.load(user_id)

    @s.field
    async def mine(self, info, user_id: str, words: t.List[str], remove: bool = False) -> Profile:
        with info.context.store.profile(int(user_id)) as profile:
            new_words = set(profile.mined_words)

            if remove:
                new_words = new_words.difference(set(words))
            else:
                new_words = new_words.union(set(words))

            profile.mined_words = sorted(new_words)

        return await info.context.dataloaders.profile.load(user_id)

    @s.field
    async def create_exam(self, info, exam: NewExam) -> t.Optional[Exam]:
        exam_doc = types.Exam(
            name=exam.name,
            num_questions=exam.num_questions,
            max_wrong=exam.max_wrong,
            timelimit=exam.timelimit,
            hsk_level=exam.hsk_level,
            deck=[
                types.Question(
                    question=q.question,
                    valid_answers=q.valid_answers,
                    meaning=q.meaning,
                )
                for q in exam.deck
            ],
        )
        info.context.store.store_exam(exam_doc)
        return await info.context.dataloaders.exam.load(exam.name)

    @s.field
    async def edit_exam(self, info, exam_name: str) -> t.Optional[ExamMutation]:
        existing_exam = await info.context.dataloaders.exam.load(exam_name)
        if existing_exam is None:
            return None
        else:
            return ExamMutation(
                name=exam_name,
            )

    @s.field
    async def set_last_bump(self, info) -> datetime:
        now = datetime.now(timezone.utc)

        server_settings = info.context.store.load_server_settings()
        server_settings.last_bump = now
        info.context.store.store_server_settings(server_settings)
        return now
