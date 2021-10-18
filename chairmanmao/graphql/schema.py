import typing as t
from datetime import datetime, timezone
from enum import Enum

from dragonmapper.transcriptions import pinyin_to_zhuyin, numbered_syllable_to_accented
import strawberry as s
import chairmanmao.store.types as types


@s.type
class DictEntry:
    simplified: str
    traditional: str
    pinyin_numbered: str
    meanings: t.List[str]

    @s.field
    def pinyin(self) -> str:
        pinyin = ' '.join(numbered_syllable_to_accented(s) for s in self.pinyin_numbered.split(' '))
        return pinyin

    @s.field
    def zhuyin(self) -> str:
        zhuyin = pinyin_to_zhuyin(self.pinyin_numbered)
        return zhuyin


@s.enum
class Role(Enum):
    Party = "Party"
    Learner = "Learner"
    Jailed = "Jailed"


@s.type
class Profile:
    user_id: str
    discord_username: str
    display_name: str
    credit: int
    hanzi: t.List[str]
    mined_words: t.List[str]
    roles: t.List[Role]
    created: datetime
    last_seen: datetime
    yuan: int
    hsk: t.Optional[int]


@s.type
class Question:
    question: str
    valid_answers: t.List[str]
    meaning: str


@s.type
class Exam:
    name: str
    num_questions: int
    max_wrong: t.Optional[int]
    timelimit: int
    hsk_level: int
    deck: t.List[Question]


@s.input
class NewQuestion:
    question: str
    valid_answers: t.List[str]
    meaning: str


@s.input
class NewExam:
    name: str
    num_questions: int
    max_wrong: t.Optional[int]
    timelimit: int
    hsk_level: int
    deck: t.List[NewQuestion]


@s.type
class ServerSettings:
    last_bump: datetime


@s.type
class AdminQuery:
    @s.field
    async def all_profiles(self, info) -> t.List[Profile]:
        assert info.context.is_admin, 'Must be admin'

        profiles = []
        for profile in info.context.store.get_all_profiles():
            profiles.append(await info.context.dataloaders.profile.load(str(profile.user_id)))
        return profiles

    @s.field
    async def server_settings(self, info) -> ServerSettings:
        server_settings = info.context.store.load_server_settings()
        return ServerSettings(
            last_bump=server_settings.last_bump
        )


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
            assert discord_username is None, 'user_id and discord_username are mutually exclusive.'
            return await info.context.dataloaders.profile.load(user_id)
        else:
            assert discord_username is not None, 'One of user_id or discord_username must be provided.'
            return await info.context.dataloaders.profile_by_discord_username.load(discord_username)

    @s.field
    async def leaderboard(self, info) -> t.List[Profile]:
        entries = []
        profiles = info.context.store.get_all_profiles()
        profiles.sort(reverse=True, key=lambda profile: profile.credit)

        for profile in profiles[:10]:
            entries.append(await info.context.dataloaders.profile.load(str(profile.user_id)))
        return entries

    @s.field
    async def exam(self, info, name: str) -> t.Optional[Exam]:
        return await info.context.dataloaders.exam.load(name)

    @s.field
    def admin(self, info) -> AdminQuery:
        assert info.context.is_admin, 'Must be admin'
        return AdminQuery()

    @s.field
    def dict(self, word: str) -> t.List[DictEntry]:
        results = []
        with open('data/cedict_ts.u8') as infile:
            for line in infile:
                if line.startswith('#'):
                    continue
                dictentry = parse_dictentry(line)
                if dictentry.simplified == word or dictentry.traditional == word:
                    results.append(dictentry)
        return results


def parse_dictentry(line: str) -> DictEntry:
    traditional, simplified, *_ = line.split(' ')
    left_brace = line.index('[')
    right_brace = line.index(']')
    pinyin_numbered = line[left_brace + 1:right_brace]

    slash = line.index('/')
    meanings = []
    try:
        while True:
            line = line[slash + 1:]
            slash = line.index('/')
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


@s.type
class AdminMutation:
    @s.field
    async def register(self, info, user_id: str, discord_username: str) -> Profile:
        assert info.context.is_admin, 'Must be admin'
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
            assert amount <= from_profile.yuan, 'Insufficient funds'
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
        assert len(name) < 32, 'Name must be 32 characters or less.'
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
                for q
                in exam.deck
            ],
        )
        info.context.store.store_exam(exam_doc)
        return await info.context.dataloaders.exam.load(exam.name)

    @s.field
    async def set_last_bump(self, info) -> datetime:
        now = datetime.now(timezone.utc)

        server_settings = info.context.store.load_server_settings()
        server_settings.last_bump = now
        info.context.store.store_server_settings(server_settings)
        return now


@s.type
class Mutation:
    @s.field
    def admin(self, info) -> AdminMutation:
        assert info.context.is_admin, 'Must be admin'
        return AdminMutation()

    @s.field
    async def set_name(self, info, name: str) -> Profile:
        assert len(name) < 32, 'Name must be 32 characters or less.'
        me = await get_me(info)
        with info.context.store.profile(int(me.user_id)) as profile:
            profile.display_name = name

        me.display_name = name
        return me


async def get_me(info) -> Profile:
    discord_username = info.context.discord_username
    return await info.context.dataloaders.profile_by_discord_username.load(discord_username)


def add_role(profile: types.Profile, role: types.Role) -> bool:
    '''
        Returns whether the profile was changed.
    '''
    roles_set = set(profile.roles)
    if role not in roles_set:
        roles_set.add(role)
        profile.roles = sorted(roles_set)
        changed = True
    else:
        changed = False

    return changed


def remove_role(profile: types.Profile, role: types.Role) -> bool:
    '''
        Returns whether the profile was changed.
    '''
    roles_set = set(profile.roles)
    if role in roles_set:
        roles_set.remove(role)
        profile.roles = sorted(roles_set)
        changed = True
    else:
        changed = False

    return changed


def set_hsk(profile: types.Profile, hsk_level: t.Optional[int]) -> None:
    role_by_level = {
        1: types.Role.Hsk1,
        2: types.Role.Hsk2,
        3: types.Role.Hsk3,
        4: types.Role.Hsk4,
        5: types.Role.Hsk5,
        6: types.Role.Hsk6,
    }

    # Remove all roles
    for role in role_by_level.values():
        remove_role(profile, role)

    if hsk_level is not None:
        # Then add the right one
        role_to_add = role_by_level[hsk_level]
        add_role(profile, role_to_add)


schema = s.Schema(
    query=Query,
    mutation=Mutation,
)
