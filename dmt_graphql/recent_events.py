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
    store = MongoDbDocumentStore(db, configuration)
    event_store = EventStore(db, configuration)

    for event in event_store.recent_events(10):
        del event['_id']
        del event['version']
        del event['created_at']
        print(event)

if __name__ == "__main__":
    main()

