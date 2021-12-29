import json
import pprint
import pymongo

from dotenv import load_dotenv

from dmt_graphql.events import Event, EventStore, EventType
from dmt_graphql.store.mongodb import MongoDbDocumentStore, create_mongodb_client
from dmt_graphql.config import Configuration


def create_legacy_event(profile):
    event = Event.new(
        EventType("LegacyProfileLoaded-1.0.0"),
        {
            'user_id': str(profile.user_id),
            'discord_username': profile.discord_username,
            'display_name': profile.display_name,
            'created': profile.created.isoformat(),
            'last_seen': profile.last_seen.isoformat(),
            'roles': [role.name for role in profile.roles],
            'credit': profile.credit,
            'yuan': profile.yuan,
            'hanzi': profile.hanzi,
            'mined_words': profile.mined_words,
            'defected': profile.defected,
        },
    )
    return event


def create_legacy_server_settings(server_settings):
    return Event.new(
        EventType("LegacyServerSettingsLoaded-1.0.0"),
        {
            "last_bump": server_settings.last_bump.isoformat(),
            "exams_disabled": server_settings.exams_disabled,
            "admin_username": server_settings.admin_username,
            "bot_username": server_settings.bot_username,
        },
    )


def assert_mirror_equivalent(store, user_id):
    std_profile = store.db.Profiles.find_one({'user_id': user_id})
    mir_profile = store.db.mirror_Profiles.find_one({'user_id': user_id})

    std_profile["_id"] = mir_profile["_id"]
    assert std_profile == mir_profile


def main():
    load_dotenv()
    configuration = Configuration.from_environment()
    db = create_mongodb_client(configuration)
    store = MongoDbDocumentStore(db, configuration)
    event_store = EventStore(db, configuration)

    event = create_legacy_server_settings(store.load_server_settings())
    event_store.push_event(event)

    for profile in store.get_all_profiles():
        print(profile.discord_username)
        event = create_legacy_event(profile)
        print()
        pprint.pprint(event.to_dict())
        print()
        print()
        event_store.push_event(event)

        assert_mirror_equivalent(store, profile.user_id)


if __name__ == "__main__":
    main()
