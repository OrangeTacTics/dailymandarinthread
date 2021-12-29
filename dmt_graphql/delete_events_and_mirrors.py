import json
import pprint
import pymongo
from dmt_graphql.events import Event, EventStore, EventType

from dmt_graphql.store.mongodb import MongoDbDocumentStore, create_mongodb_client
from dmt_graphql.config import Configuration
from dotenv import load_dotenv


def main():
    load_dotenv()
    configuration = Configuration.from_environment()
    db = create_mongodb_client(configuration)
    store = MongoDbDocumentStore(db, configuration, mirror=True)
    event_store = EventStore(db, configuration)

    event_store.events.delete_many({})
    store.profiles.delete_many({})
    store.server_settings.delete_many({})

if __name__ == "__main__":
    main()

