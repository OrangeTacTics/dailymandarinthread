import json
import pprint
import pymongo
from dmt_graphql.events import Event, EventStore, EventType

from dmt_graphql.store.mongodb import MongoDbDocumentStore
from dmt_graphql.config import Configuration
from dotenv import load_dotenv

load_dotenv()

configuration = Configuration.from_environment()


def create_legacy_event(profile):
    event = Event.new(
        EventType("LegacyProfileLoaded", "1.0.0"),
        {
            'user_id': str(profile.user_id),
            'discord_username': profile.discord_username,
            'display_name': profile.display_name,
            'created': profile.created,
            'last_seen': profile.last_seen,
            'roles': [role.name for role in profile.roles],
            'credit': profile.credit,
            'yuan': profile.yuan,
            'hanzi': profile.hanzi,
            'mined_words': profile.mined_words,
            'defected': profile.defected,
        },
    )
    return event


def main():
    store = MongoDbDocumentStore(configuration)

    for profile in store.get_all_profiles():
        print(profile.discord_username)
        event = create_legacy_event(profile)
        print()
        pprint.pprint(event.to_dict())
        print()
        print()
        event_store = EventStore(configuration)
        event_store.push(event)



if __name__ == "__main__":
    main()
