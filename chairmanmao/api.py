from __future__ import annotations
import typing as t
from dataclasses import dataclass

from datetime import datetime, timezone

import chairmanmao.types as cmt

from chairmanmao.store import DocumentStore
from chairmanmao.store.types import Profile, Role


UserId = int


@dataclass
class LeaderboardEntry:
    display_name: str
    credit: int


@dataclass
class SyncInfo:
    user_id: UserId
    display_name: str
    credit: int
    roles: t.Set[cmt.Role]
    hsk_level: t.Optional[int]


@dataclass
class Api:
    store: DocumentStore

    def as_chairman(self) -> ChairmanApi:
        return ChairmanApi(
            store=self.store,
        )

    def as_party(self, user_id: UserId) -> PartyApi:
        return PartyApi(
            store=self.store,
            user_id=user_id,
        )

    def as_comrade(self, user_id: UserId) -> ComradeApi:
        return ComradeApi(
            store=self.store,
            user_id=user_id,
        )


@dataclass
class ChairmanApi:
    store: DocumentStore

    def is_registered(self, user_id: UserId) -> bool:
        profile = self.store.load_profile(user_id)
        return profile is not None

    def register(self, user_id: UserId, discord_username: str) -> None:
        self.store.create_profile(user_id, discord_username)

    def get_sync_info(self, user_id: UserId) -> SyncInfo:
        profile = self.store.load_profile(user_id)
        hsk_level = _hsk_level(profile)

        cmt_roles = []
        for role in profile.roles:
            cmt_role = profile_role_to_cmt_role(role)
            if cmt_role is not None:
                cmt_roles.append(cmt_role)

        return SyncInfo(
            user_id=profile.user_id,
            display_name=profile.display_name,
            credit=profile.credit,
            roles=set(cmt_roles),
            hsk_level=hsk_level,
        )

    def honor(self, user_id: UserId, credit: int) -> int:
        assert credit > 0

        with self.store.profile(user_id) as profile:
            profile.credit += credit
            return profile.credit

    def dishonor(self, user_id: UserId, credit: int) -> int:
        assert credit > 0
        with self.store.profile(user_id) as profile:
            profile.credit -= credit
            return profile.credit

    def set_name(self, user_id: UserId, name: str) -> None:
        assert len(name) < 32, 'Name must be 32 characters or less.'
        with self.store.profile(user_id) as profile:
            profile.display_name = name

    def list_users(self) -> t.List[UserId]:
        user_ids = []
        for profile in self.store.get_all_profiles():
            user_ids.append(profile.user_id)
        return user_ids

    def promote(self, user_id: UserId) -> None:
        with self.store.profile(user_id) as profile:
            if Role.Party not in profile.roles:
                profile.roles.append(Role.Party)
                profile.roles.sort()
            else:
                raise Exception("Already a party member")

    def demote(self, user_id: UserId) -> None:
        with self.store.profile(user_id) as profile:
            if Role.Party in profile.roles:
                profile.roles.remove(Role.Party)
                profile.roles.sort()
            else:
                raise Exception("Not a party member")

    def get_hsk(self, user_id: UserId) -> t.Optional[int]:
        level_by_role = {
            Role.Hsk1: 1,
            Role.Hsk2: 2,
            Role.Hsk3: 3,
            Role.Hsk4: 4,
            Role.Hsk5: 5,
            Role.Hsk6: 6,
        }

        profile = self.store.load_profile(user_id)
        for role, level in level_by_role.items():
            if role in profile.roles:
                return level

        return None

    def set_hsk(self, user_id: UserId, hsk_level: t.Optional[int]) -> None:
        role_by_level = {
            1: Role.Hsk1,
            2: Role.Hsk2,
            3: Role.Hsk3,
            4: Role.Hsk4,
            5: Role.Hsk5,
            6: Role.Hsk6,
        }

        with self.store.profile(user_id) as profile:
            # Remove all roles
            for role in role_by_level.values():
                remove_role(profile, role)

            if hsk_level is not None:
                # Then add the right one
                role_to_add = role_by_level[hsk_level]
                add_role(profile, role_to_add)


@dataclass
class PartyApi:
    store: DocumentStore
    user_id: UserId

    def jail(self, user_id: UserId) -> None:
        with self.store.profile(user_id) as profile:
            if Role.Jailed not in profile.roles:
                profile.roles.append(Role.Jailed)
                profile.roles.sort()
            else:
                raise Exception("Already jailed")

    def unjail(self, user_id: UserId) -> None:
        with self.store.profile(user_id) as profile:
            if Role.Jailed in profile.roles:
                profile.roles = sorted(role for role in profile.roles if role != Role.Jailed)
            else:
                raise Exception("Not jailed")

    def stepdown(self) -> None:
        with self.store.profile(self.user_id) as profile:
            if Role.Party in profile.roles:
                profile.roles = sorted(role for role in profile.roles if role != Role.Party)
            else:
                raise Exception("Not a party member")


@dataclass
class ComradeApi:
    store: DocumentStore
    user_id: UserId

    def get_discord_username(self, user_id: UserId) -> str:
        profile = self.store.load_profile(user_id)
        return profile.discord_username

    def get_display_name(self, user_id: UserId) -> str:
        profile = self.store.load_profile(user_id)
        return profile.display_name

    def social_credit(self, user_id: UserId) -> int:
        profile = self.store.load_profile(user_id)
        assert profile is not None
        return profile.credit

    def set_learner(self, flag: bool) -> None:
        with self.store.profile(self.user_id) as profile:
            if flag:
                profile.roles.append(Role.Learner)
            else:
                profile.roles = [role for role in profile.roles if role != Role.Learner]

            profile.roles = sorted(set(profile.roles))

    def draw(self, font_name: str, text: str) -> None:
        ...

    def upload_font(self, font_name: str, font_data: bytes) -> None:
        ...

    def mine(self, word: str) -> None:
        with self.store.profile(self.user_id) as profile:
            profile.mined_words.append(word)
            profile.mined_words = sorted(set(profile.mined_words))

    def get_mined(self) -> t.List[str]:
        profile = self.store.load_profile(self.user_id)
        assert profile is not None, f"No profile exists for {self.user_id}"
        return profile.mined_words

    def yuan(self) -> int:
        profile = self.store.load_profile(self.user_id)
        assert profile is not None, f"No profile exists for {self.user_id}"
        return profile.yuan

    def leaderboard(self) -> t.List[LeaderboardEntry]:
        entries = []
        profiles = self.store.get_all_profiles()
        profiles.sort(reverse=True, key=lambda profile: profile.credit)

        for profile in profiles[:10]:
            entries.append(LeaderboardEntry(
                display_name=profile.display_name,
                credit=profile.credit,
            ))
        return entries

    def set_name(self, name: str) -> None:
        assert len(name) < 32, 'Name must be 32 characters or less.'
        with self.store.profile(self.user_id) as profile:
            profile.display_name = name

    def get_name(self) -> str:
        profile = self.store.load_profile(self.user_id)
        assert profile is not None, f"No profile exists for {self.user_id}"
        return profile.display_name

    def last_seen(self, user_id: UserId) -> datetime:
        profile = self.store.load_profile(user_id)
        assert profile is not None, f"No profile exists for {self.user_id}"
        last_seen = profile.last_seen
        last_seen = last_seen.replace(tzinfo=timezone.utc)
        last_seen = last_seen.replace(microsecond=0)
        return last_seen

    def alert_activity(self) -> None:
        with self.store.profile(self.user_id) as profile:
            profile.last_seen = datetime.now(timezone.utc).replace(microsecond=0)


def add_role(profile: Profile, role: Role) -> bool:
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


def remove_role(profile: Profile, role: Role) -> bool:
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


def _hsk_level(profile: Profile) -> t.Optional[int]:
    if Role.Hsk1 in profile.roles:
        return 1
    elif Role.Hsk2 in profile.roles:
        return 2
    elif Role.Hsk3 in profile.roles:
        return 3
    elif Role.Hsk4 in profile.roles:
        return 4
    elif Role.Hsk5 in profile.roles:
        return 5
    elif Role.Hsk6 in profile.roles:
        return 6
    else:
        return None


def profile_role_to_cmt_role(role: Role) -> t.Optional[cmt.Role]:
    cmt_roles = {
        Role.Comrade: cmt.Role.Comrade,
        Role.Party: cmt.Role.Party,
        Role.Learner: cmt.Role.Learner,
        Role.Jailed: cmt.Role.Jailed,
        Role.Hsk1: cmt.Role.Hsk1,
        Role.Hsk2: cmt.Role.Hsk2,
        Role.Hsk3: cmt.Role.Hsk3,
        Role.Hsk4: cmt.Role.Hsk4,
        Role.Hsk5: cmt.Role.Hsk5,
        Role.Hsk6: cmt.Role.Hsk6,
    }
    return cmt_roles[role]
