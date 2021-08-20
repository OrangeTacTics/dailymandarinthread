import os
import pymongo
from dotenv import load_dotenv

load_dotenv()


MONGODB_URL = os.getenv('MONGODB_URL')
MONGODB_DB = os.getenv('MONGODB_DB')


SCHEMA_VERSION = 0


if __name__ == "__main__":
    client = pymongo.MongoClient(MONGODB_URL)
    db = client[MONGODB_DB]

    for old_schema_version in range(SCHEMA_VERSION):
        query = { "schema_version": old_schema_version }
        old_profiles = list(db['Profiles'].find(query))
        assert len(old_profiles) == 0, f'Found {len(old_profiles)} with schema_version = {old_schema_version}'

    for record in db['Profiles'].find({}):
        if type(record['_id']) != ObjectId:
            print(
