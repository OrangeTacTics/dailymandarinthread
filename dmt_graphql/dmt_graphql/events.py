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

class EventValueError(Exception):
    pass


EventValidator = t.Callable[[t.Any], None]


class EventType:
    name: str
    version: Version

    def __init__(self, name: str, version: t.Optional[str] = None) -> None:
        if version is None:
            versions: t.Set[Version] = {
                v for n, v in EVENT_TYPES.keys() if n == name
            }
            vversion = max(versions)
        else:
            vversion = Version(version)


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
            return EventType(name, version)

        return wrapper

    @staticmethod
    def all() -> t.List[EventType]:
        return [EventType(name, str(version)) for (name, version) in EVENT_TYPES.keys()]

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
            type=EventType(type, version),
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


class EventStore:
    def __init__(self, configuration: Configuration) -> None:
        self.configuration = configuration
        self.mongo_client = pymongo.MongoClient(
            host=configuration.MONGODB_URL,
#            username=configuration.MONGODB_USER,
#            password=configuration.MONGODB_PASS,
#            tlsCAFile=configuration.MONGODB_CERT,
        )
        db = self.mongo_client[configuration.MONGODB_DB]
        self.events = db["Events"]

    def push(self, event: Event) -> None:
        event.validate()
        self.events.insert_one(event.to_dict())



@EventType.register("LegacyProfileLoaded", "1.0.0")
def legacy_profile_loaded_1_0_0(payload: t.Any) -> None:
    assert isinstance(payload["user_id"], str)
    assert isinstance(payload["discord_username"], str)
    assert isinstance(payload["display_name"], str)
    assert isinstance(payload["created"], datetime)
    assert isinstance(payload["last_seen"], datetime)
    assert isinstance(payload["roles"], list)
    assert all(isinstance(x, str) for x in payload["roles"])
    assert isinstance(payload["credit"], int)
    assert isinstance(payload["yuan"], int)
    assert isinstance(payload["hanzi"], list)
    assert all(isinstance(x, str) for x in payload["hanzi"])
    assert all(isinstance(x, str) for x in payload["mined_words"])
    assert isinstance(payload["defected"], bool)
