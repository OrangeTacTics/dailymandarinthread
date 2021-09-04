from __future__ import annotations
import typing as t
from dataclasses import dataclass

import os

from dotenv import load_dotenv
import jwt
import pymongo

from chairmanmao.types import Profile
from chairmanmao.profile import get_profile, create_profile, set_profile_last_message, get_all_profiles, open_profile

#from chairmanmao.hanzi import get_seen_hanzi, see_hanzi
#from chairmanmao.draw import draw, get_font_names
#from chairmanmao.fourchan import get_dmt_thread, is_url_seen, see_url


UserId = str


#class Rank:
#    CHAIRMAN
#    PARTY_MEMBER
#    COMRADE


@dataclass
class LeaderboardEntry:
    display_name: str
    credit: int


@dataclass
class Api:
    db: pymongo.MongoClient

    @staticmethod
    def connect(mongo_url: str, mongo_db: str) -> Api:
        mongo_client = pymongo.MongoClient(mongo_url)
        db = mongo_client[mongo_db]
        return Api(
            db=db,
        )

    def as_chairman(self, user_id: UserId) -> ChairmanApi:
        return ChairmanApi(
            db=self.db,
            user_id=user_id,
        )

    def as_party(self, user_id: UserId) -> PartyApi:
        return PartyApi(
            db=self.db,
            user_id=user_id,
        )

    def as_comrade(self, user_id: UserId) -> ComradeApi:
        return ComradeApi(
            db=self.db,
            user_id=user_id,
        )


@dataclass
class ChairmanApi:
    db: pymongo.MongoClient
    user_id: UserId

    def honor(self, user_id: UserId, credit: int) -> int:
        assert credit > 0
        with open_profile(self.db, user_id) as profile:
            profile.credit += credit
            return profile.credit

    def dishonor(self, user_id: UserId, credit: int) -> int:
        assert credit > 0
        with open_profile(self.db, user_id) as profile:
            profile.credit -= credit
            return profile.credit

    def set_name(self, user_id: UserId, name: str) -> None:
        assert len(name) < 32, 'Name must be 32 characters or less.'
        with open_profile(self.db, user_id) as profile:
            profile.display_name = name


@dataclass
class PartyApi:
    db: pymongo.MongoClient
    user_id: UserId

    def recognize(self, user_id, credit: int) -> None:
        ...

    def stepdown(self) -> None:
        ...


@dataclass
class ComradeApi:
    db: pymongo.MongoClient
    user_id: UserId

    @staticmethod
    def connect(mongo_url: str, mongo_db: str, user_id: UserId) -> ComradeApi:
        mongo_client = pymongo.MongoClient(MONGODB_URL)
        db = mongo_client[mongo_db]
        return ComradeApi(
            db=db,
            user_id=user_id,
        )

    def social_credit(self, user_id: UserId) -> int:
        profile = get_profile(self.db, user_id)
        assert profile is not None
        return profile.credit

    def set_learner(self, flag: bool) -> None:
        ...

    def draw(self, font_name: str, text: str) -> None:
        ...

    def upload_font(self, font_name: str, font_data: bytes) -> None:
        ...

    def mine(self, word: str) -> None:
        with open_profile(self.db, self.user_id) as profile:
            profile.mined_words.append(word)
            profile.mined_words = sorted(set(profile.mined_words))

    def get_mined(self) -> t.List[str]:
        profile = get_profile(self.db, self.user_id)
        assert profile is not None, f"No profile exists for {self.user_id}"
        return profile.mined_words

    def get_hanzi(self, user_id: UserId) -> t.List[str]:
        profile = get_profile(self.db, user_id)
        assert profile is not None, f"No profile exists for {user_id}"
        return profile.hanzi

    def yuan(self) -> int:
        profile = get_profile(self.db, self.user_id)
        assert profile is not None, f"No profile exists for {self.user_id}"
        return profile.yuan

    def leaderboard(self) -> t.List[LeaderboardEntry]:
        entries = []
        profiles = get_all_profiles(self.db)
        profiles.sort(reverse=True, key=lambda profile: profile.credit)

        for profile in profiles[:10]:
            entries.append(LeaderboardEntry(
                display_name=profile.display_name,
                credit=profile.credit,
            ))
        return entries

    def set_name(self, name: str) -> None:
        assert len(name) < 32, 'Name must be 32 characters or less.'
        with open_profile(self.db, self.user_id) as profile:
            profile.display_name = name

    def get_name(self) -> str:
        profile = get_profile(self.db, self.user_id)
        assert profile is not None, f"No profile exists for {self.user_id}"
        return profile.display_name


if __name__ == '__main__':
    load_dotenv()

    MONGODB_URL = os.getenv('MONGODB_URL', '')
    MONGODB_DB = os.getenv('MONGODB_DB', '')

    username =  'OrangeTacTics#0949'

    api = Api.connect(MONGODB_URL, MONGODB_DB)
    chairman_api = api.as_chairman(username)
    comrade_api = api.as_comrade(username)

    print('credit:', comrade_api.social_credit('OrangeTacTics#0949'))

    comrade_api.mine('猫')

    for word in comrade_api.get_mined():
        print('-', word)

    print()
    print('Yuan:', comrade_api.yuan())

    for hanzi in comrade_api.get_hanzi(username)[:3]:
        print('-', hanzi)

    print('Display name:', comrade_api.get_name())
    comrade_api.set_name(username)
    print('Display name:', comrade_api.get_name())
    print()

    lines = [
        "The DMT Leaderboard",
        "```",
    ]
    for entry in comrade_api.leaderboard():
        line = f'{entry.credit} ... {entry.display_name}'
        lines.append(line)

    lines.append("```")
    print('\n'.join(lines))


    snickers = 'Snickers#0486'
    print('Snickers credit:', comrade_api.social_credit(snickers))
    print('dishonor 10...')
    chairman_api.dishonor(snickers, 10)
    print('Snickers credit:', comrade_api.social_credit(snickers))
    print('honor 11...')
    chairman_api.honor(snickers, 11)
    print('Snickers credit:', comrade_api.social_credit(snickers))
