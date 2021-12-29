from __future__ import annotations

import typing as t
import json
from dataclasses import dataclass
from datetime import datetime
from datetime import timezone

from semantic_version import Version
from ulid import ULID
import pymongo

from dmt_graphql.config import Configuration
from dmt_graphql.store.types import ServerSettings


class EventValueError(Exception):
    pass


EventValidator = t.Callable[[t.Any], None]


class EventType:
    name: str
    version: Version

    def __init__(self, name_version: str) -> None:
        name, version = name_version.split('-')
        vversion = Version(version)
        assert (name, vversion) in EVENT_TYPES, f"No such event: {name}-{version}"
        self.name = name
        self.version = vversion

    def __eq__(self, other) -> bool:
        return (self.name, self.version) == (other.name, other.version)

    def __hash__(self):
        return hash((self.name, str(self.version)))

    def __str__(self) -> str:
        return f'{self.name}-{self.version}'

    def __repr__(self) -> str:
        return f'{self.name}-{self.version}'

    @staticmethod
    def register(name: str, version: str) -> t.Callable[[t.Any], EventType]:
        def wrapper(validator: EventValidator) -> EventType:
            vversion = Version(version)
            assert (name, vversion) not in EVENT_TYPES, "Event is already defined"
            EVENT_TYPES[name, vversion] = validator
            return EventType(f"{name}-{version}")

        return wrapper

    @staticmethod
    def all() -> t.List[EventType]:
        return [EventType(f"{name}-{version}") for (name, version) in EVENT_TYPES.keys()]

    def validator(self, payload: t.Any) -> None:
        validator = EVENT_TYPES[self.name, self.version]
        validator(payload)


EVENT_TYPES: t.Dict[t.Tuple[str, Version], EventValidator] = {}


@dataclass
class Event:
    id: ULID
    type: EventType
    created_at: datetime
    payload: t.Any

    @staticmethod
    def new(
        type: EventType,
        payload: t.Any,
        *,
        validate: bool = True,
    ) -> Event:
        now = datetime.now(timezone.utc)
        id = ULID.from_datetime(now)
        event = Event(
            id=id,
            type=type,
            created_at=now,
            payload=payload,
        )

        if validate:
            event.validate()

        return event

    def to_dict(self) -> t.Dict[str, t.Any]:
        return {
            "id": str(self.id),
            "type": self.type.name,
            "version": str(self.type.version),
            "created_at": self.created_at.isoformat(),
            "payload": self.payload,
        }

    @staticmethod
    def from_json(json_str: str) -> Event:
        event_json = json.loads(json_str)

        id = ULID.from_str(event_json["id"])
        type = event_json["type"]
        version = event_json["version"]
        created_at = datetime.fromisoformat(event_json["created_at"])
        payload = event_json["payload"]

        event = Event(
            id=id,
            type=EventType(f"{type}-{version}"),
            created_at=created_at,
            payload=payload,
        )

        #event.validate()
        return event

    def validate(self) -> None:
        try:
            self.type.validator(self.payload)
        except Exception as e:
            if len(e.args) > 0:
                error_message = e.args[0]
                raise EventValueError(error_message) from e
            else:
                raise EventValueError() from e

    def __lt__(self, other):
        return (self.created_at, self.id) < (other.created_at, self.id)

def handler_LegacyServerSettingsLoaded(store, event):
    server_settings = ServerSettings(
        last_bump=datetime.fromisoformat(event.payload['last_bump']),
        exams_disabled=event.payload['exams_disabled'],
        admin_username=event.payload['admin_username'],
        bot_username=event.payload['bot_username'],
    )
    store.store_server_settings(server_settings)


def handler_LegacyProfileLoaded(store, event):
    from dmt_graphql.store.types import Role

    profile = store.create_profile(
        int(event.payload["user_id"]),
        event.payload["discord_username"],
    )

    profile.user_id = int(event.payload['user_id'])
    profile.discord_username = event.payload['discord_username']
    profile.display_name = event.payload['display_name']
    profile.created = datetime.fromisoformat(event.payload['created'])
    profile.last_seen = datetime.fromisoformat(event.payload['last_seen'])
    profile.roles = [Role.from_str(role) for role in event.payload['roles']]
    profile.credit = event.payload['credit']
    profile.yuan = event.payload['yuan']
    profile.hanzi = event.payload['hanzi']
    profile.mined_words = event.payload['mined_words']
    profile.defected = event.payload['defected']

    store.store_profile(profile)

    print(profile)
    print(event)


def handler_ActivityAlerted(store, event):
    for user_id in event.payload["user_ids"]:
        with store.profile(int(user_id)) as profile:
            profile.last_seen = event.created_at
            profile.defected = False


def handler_RmbTransferred(store, event):
    from_user_id = event.payload["from_user_id"]
    to_user_id = event.payload["to_user_id"]
    amount = event.payload["amount"]

    with store.profile(int(from_user_id)) as from_profile:
        from_profile.yuan -= amount

    with store.profile(int(to_user_id)) as to_profile:
        to_profile.yuan += amount


def handler_ServerBumped(store, event):
    server_settings = store.load_server_settings()
    server_settings.last_bump = event.created_at
    store.store_server_settings(server_settings)


class EventStore:
    def __init__(self, db, configuration: Configuration) -> None:
        self.events = db["Events"]

        from dmt_graphql.store.mongodb import MongoDbDocumentStore
        self.store = MongoDbDocumentStore(db, configuration, mirror=True)

    def push(self, event_type: str, payload: t.Any) -> None:
        event = Event.new(EventType(event_type), payload)
        self.push_event(event)

    def push_event(self, event: Event) -> None:
        handler = {
            EventType("LegacyServerSettingsLoaded-1.0.0"): handler_LegacyServerSettingsLoaded,
            EventType("LegacyProfileLoaded-1.0.0"): handler_LegacyProfileLoaded,
            EventType("ActivityAlerted-1.0.0"): handler_ActivityAlerted,
            EventType("RmbTransferred-1.0.0"): handler_RmbTransferred,
            EventType("ServerBumped-1.0.0"): handler_ServerBumped,
        }[event.type]
        self.events.insert_one(event.to_dict())
        handler(self.store, event)

    def recent_events(self, count: int) -> t.List[Event]:
        return list(self.events.aggregate([
            {"$sort": {"id": -1}},
            {"$limit": count},
        ]))


@EventType.register("LegacyServerSettingsLoaded", "1.0.0")
def legacy_server_settings_loaded_1_0_0(payload: t.Any) -> None:
    _ = datetime.fromisoformat(payload["last_bump"])
    assert isinstance(payload["exams_disabled"], bool)
    assert isinstance(payload["admin_username"], str)
    assert isinstance(payload["bot_username"], str)


@EventType.register("LegacyProfileLoaded", "1.0.0")
def legacy_profile_loaded_1_0_0(payload: t.Any) -> None:
    assert isinstance(payload["user_id"], str)
    assert isinstance(payload["discord_username"], str)
    assert isinstance(payload["display_name"], str)
    assert isinstance(payload["created"], str)
    _ = datetime.fromisoformat(payload["created"])
    assert isinstance(payload["last_seen"], str)
    _ = datetime.fromisoformat(payload["last_seen"])
    assert isinstance(payload["roles"], list)
    assert all(isinstance(x, str) for x in payload["roles"])
    assert isinstance(payload["credit"], int)
    assert isinstance(payload["yuan"], int)
    assert isinstance(payload["hanzi"], list)
    assert all(isinstance(x, str) for x in payload["hanzi"])
    assert all(isinstance(x, str) for x in payload["mined_words"])
    assert isinstance(payload["defected"], bool)


@EventType.register("ActivityAlerted", "1.0.0")
def activity_alerted_1_0_0(payload: t.Any) -> None:
    assert isinstance(payload["user_ids"], list)
    assert all(isinstance(x, str) for x in payload["user_ids"])


@EventType.register("RmbTransferred", "1.0.0")
def rmb_transferred_1_0_0(payload: t.Any) -> None:
    assert isinstance(payload["from_user_id"], str)
    assert isinstance(payload["to_user_id"], str)
    assert payload["from_user_id"] != payload["to_user_id"]
    assert isinstance(payload["amount"], int)
    assert payload["amount"] > 0
    assert payload["message"] is None or isinstance(payload["message"], str)


@EventType.register("ServerBumped", "1.0.0")
def server_bumped_1_0_0(payload: t.Any) -> None:
    assert isinstance(payload["user_id"], str)

#@EventType.register("ComradeChangedName", "1.0.0")
#def comrade_changed_name_1_0_0(payload: t.Any) -> None:
#    pass

#@EventType.register("AdminChangedComradeName", "1.0.0")
#def admin_changed_comrade_name_1_0_0(payload: t.Any) -> None:
#    pass

#@EventType.register("ComradeJoined", "1.0.0")
#def comrade_joined_1_0_0(payload: t.Any) -> None:
#    pass
#
#@EventType.register("ComradeDefected", "1.0.0")
#def comrade_defected_1_0_0(payload: t.Any) -> None:
#    pass
#
#@EventType.register("ComradeHonored", "1.0.0")
#def comrade_honored_1_0_0(payload: t.Any) -> None:
#    pass
#
#@EventType.register("ComradeDishonored", "1.0.0")
#def comrade_dishonored_1_0_0(payload: t.Any) -> None:
#    pass
#
#@EventType.register("ComradeJailed", "1.0.0")
#def comrade_jailed_1_0_0(payload: t.Any) -> None:
#    pass
#
#@EventType.register("ComradeUnjailed", "1.0.0")
#def comrade_unjailed_1_0_0(payload: t.Any) -> None:
#    pass
#
#@EventType.register("ComradePromotedToParty", "1.0.0")
#def comrade_promoted_to_party_1_0_0(payload: t.Any) -> None:
#    pass
#
#@EventType.register("ComradeDemotedFromParty", "1.0.0")
#def comrade_demoted_from_party_1_0_0(payload: t.Any) -> None:
#    pass
#
#@EventType.register("WordMined", "1.0.0")
#def word_mined_1_0_0(payload: t.Any) -> None:
#    pass
#
#@EventType.register("ExamsDisabled", "1.0.0")
#def exams_disabled_1_0_0(payload: t.Any) -> None:
#    pass
#
#@EventType.register("ExamsEnabled", "1.0.0")
#def exams_enabled_1_0_0(payload: t.Any) -> None:
#    pass
#
#@EventType.register("ExamStarted", "1.0.0")
#def exam_started_1_0_0(payload: t.Any) -> None:
#    pass
#
#@EventType.register("ExamEnded", "1.0.0")
#def exam_ended_1_0_0(payload: t.Any) -> None:
#    pass
