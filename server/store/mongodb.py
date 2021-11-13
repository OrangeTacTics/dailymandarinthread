from __future__ import annotations
import typing as t
import os
from datetime import timezone, timedelta, datetime

import pymongo
from bson.objectid import ObjectId

from .types import Profile, Role, Json, UserId, ServerSettings, Exam, Question, DictEntry


class MongoDbDocumentStore:
    def __init__(self, mongo_url: str, mongo_db: str) -> None:
        self.mongo_client = pymongo.MongoClient(mongo_url)
        self.db = self.mongo_client[mongo_db]
        self.profiles = self.db["Profiles"]
        self.server_settings = self.db["ServerSettings"]
        self.exams = self.db["Exams"]
        self.dict_entries = self.db["DictEntries"]

    def profile(self, user_id: UserId) -> "OpenProfileContextManager":
        return OpenProfileContextManager(self, user_id)

    def create_profile(self, user_id: UserId, discord_username: str) -> Profile:
        profile = Profile.make(user_id, discord_username)

        assert not self.profile_exists(user_id)

        if discord_username == os.environ["BOT_USERNAME"]:
            profile.yuan = 10000

        self.profiles.insert_one(profile_to_json(profile))
        return profile

    def profile_exists(self, user_id: UserId) -> bool:
        return len(list(self.profiles.find({"user_id": user_id}))) > 0

    def load_profile_by_discord_username(self, discord_username: str) -> Profile:
        profile_json = self.profiles.find_one({"discord_username": discord_username})
        return profile_from_json(profile_json)

    def load_profile(self, user_id: UserId) -> Profile:
        profile_json = self.profiles.find_one({"user_id": user_id})
        return profile_from_json(profile_json)

    def store_profile(self, profile: Profile) -> None:
        query = {"user_id": profile.user_id}
        self.profiles.replace_one(query, profile_to_json(profile))

    def get_all_profiles(self) -> t.List[Profile]:
        return [profile_from_json(p) for p in self.profiles.find({})]

    def leaderboard(self) -> t.List[Profile]:
        profiles = self.profiles.aggregate(
            [
                {"$sort": {"credit": -1}},
                {"$limit": 10},
            ]
        )
        return [profile_from_json(p) for p in profiles]

    def profile_count(self) -> int:
        return self.profiles.count_documents({})

    def active_profile_count(self) -> int:
        now = datetime.now(timezone.utc)
        a_week_ago = now - timedelta(days=7)

        results = self.profiles.aggregate(
            [
                {
                    "$match": {
                        "last_seen": {"$gte": a_week_ago},
                        "credit": {"$gte": 1010},
                    },
                },
                {
                    "$count": "count",
                },
            ]
        )
        return list(results)[0]["count"]

    def get_exam_names(self) -> t.List[str]:
        return [
            exam["name"]
            for exam in self.exams.aggregate(
                [
                    {"$project": {"name": 1, "_id": 0}},
                ]
            )
        ]

    def load_exam(self, exam_name: str) -> t.Optional[Exam]:
        exam_json = self.exams.find_one({"name": exam_name})
        if exam_json is not None:
            return exam_from_json(exam_json)
        else:
            return None

    def store_exam(self, exam: Exam) -> None:
        query = {"name": exam.name}
        self.exams.replace_one(query, exam_to_json(exam), upsert=True)

    def load_server_settings(self) -> ServerSettings:
        json_data = self.server_settings.find_one({})
        return ServerSettings(
            last_bump=json_data["last_bump"].replace(tzinfo=timezone.utc),
            exams_disabled=json_data.get("exams_disabled", False),
            admin_username=json_data.get("admin_username", os.environ["ADMIN_USERNAME"]),
            bot_username=json_data.get("bot_username", os.environ["BOT_USERNAME"]),
        )

    def store_server_settings(self, server_settings: ServerSettings) -> None:
        doc = {
            "last_bump": server_settings.last_bump,
            "exams_disabled": server_settings.exams_disabled,
            "admin_username": server_settings.admin_username,
            "bot_username": server_settings.bot_username,
        }
        self.server_settings.replace_one({}, doc)

    def dict_entry_lookup(self, query: str) -> t.List[DictEntry]:
        docs = self.dict_entries.aggregate(
            [
                {
                    "$match": {
                        "$or": [
                            {"traditional": query},
                            {"simplified": query},
                        ]
                    }
                }
            ]
        )
        return [dict_entry_from_json(doc) for doc in docs]


def profile_to_json(profile: Profile) -> Json:
    roles = [role.value for role in profile.roles]
    return {
        "user_id": profile.user_id,
        "discord_username": profile.discord_username,
        "created": profile.created,
        "last_seen": profile.last_seen,
        "roles": roles,
        "display_name": profile.display_name,
        "credit": profile.credit,
        "yuan": profile.yuan,
        "hanzi": [],
        "mined_words": profile.mined_words,
        "defected": profile.defected,
    }


def profile_from_json(profile_json: Json) -> Profile:
    roles = [Role.from_str(role) for role in profile_json["roles"]]
    return Profile(
        user_id=profile_json["user_id"],
        discord_username=profile_json["discord_username"],
        created=profile_json["created"],
        last_seen=profile_json["last_seen"],
        roles=roles,
        display_name=profile_json["display_name"],
        credit=profile_json["credit"],
        hanzi=profile_json["hanzi"],
        mined_words=profile_json["mined_words"],
        yuan=profile_json["yuan"],
        defected=profile_json["defected"],
    )


def exam_to_json(exam: Exam) -> Json:
    return {
        "name": exam.name,
        "num_questions": exam.num_questions,
        "max_wrong": exam.max_wrong,
        "timelimit": exam.timelimit,
        "hsk_level": exam.hsk_level,
        "deck": [question_to_json(q) for q in exam.deck],
    }


def question_to_json(question: Question) -> Json:
    return {
        "question": question.question,
        "valid_answers": question.valid_answers,
        "meaning": question.meaning,
    }


def exam_from_json(exam_json: Json) -> Exam:
    return Exam(
        name=exam_json["name"],
        num_questions=exam_json["num_questions"],
        max_wrong=exam_json["max_wrong"],
        timelimit=exam_json["timelimit"],
        hsk_level=exam_json["hsk_level"],
        deck=[question_from_json(q) for q in exam_json["deck"]],
    )


def question_from_json(question_json: Json) -> Question:
    return Question(
        question=question_json["question"],
        valid_answers=question_json["valid_answers"],
        meaning=question_json["meaning"],
    )


def dict_entry_to_json(dict_entry: DictEntry) -> Json:
    return {
        "_id": ObjectId(dict_entry.dict_entry_id),
        "simplified": dict_entry.simplified,
        "traditional": dict_entry.traditional,
        "pinyin": dict_entry.pinyin,
        "meanings": dict_entry.meanings,
    }


def dict_entry_from_json(dict_entry: Json) -> DictEntry:
    return DictEntry(
        dict_entry_id=str(dict_entry["_id"]),
        simplified=dict_entry["simplified"],
        traditional=dict_entry["traditional"],
        pinyin=dict_entry["pinyin"],
        meanings=dict_entry["meanings"],
    )


class OpenProfileContextManager:
    def __init__(self, store: MongoDbDocumentStore, user_id: UserId) -> None:
        self.store = store
        self.user_id = user_id
        self.profile: t.Optional[Profile] = None

    def __enter__(self) -> Profile:
        self.profile = self.store.load_profile(self.user_id)
        return self.profile

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        assert self.profile is not None
        assert self.profile.user_id == self.user_id
        self.store.store_profile(self.profile)
