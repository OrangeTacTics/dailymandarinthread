# flake8: noqa
import time
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

    seen_ids = set()

    try:
        while True:
            for event in reversed(event_store.recent_events(100)):
                del event["_id"]
                del event["version"]
                del event["created_at"]

                if event["id"] not in seen_ids:
                    seen_ids.add(event["id"])
                    pprint.pprint(event)
                    print()
                    #print(event["id"])

            time.sleep(1)

    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
