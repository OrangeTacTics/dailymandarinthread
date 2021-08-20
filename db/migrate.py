import os
import pymongo
from dotenv import load_dotenv

import db.migrations.migration_0000_objectids_not_memberids as m0000
import db.migrations.migration_0001_created_last_message_yuan as m0001

load_dotenv()


MONGODB_TEST_URL = os.getenv('MONGODB_TEST_URL')
MONGODB_TEST_DB = os.getenv('MONGODB_TEST_DB')


def connect():
    client = pymongo.MongoClient(MONGODB_URL)
    db = client[MONGODB_DB]
    return db


def apply(db, transform, old_version):
    new_version = old_version + 1
    profile_col = db['Profiles']

    cursor = profile_col.find({"schema_version": old_version})
    for old_profile in cursor:
        id = old_profile['_id']
        new_profile = transform(old_profile)
        new_profile['schema_version'] = new_version
        profile_col.delete_one({'_id': id})
        profile_col.insert_one(new_profile)


MIGRATIONS = [
    m0000,
    m0001,
]

if __name__ == "__main__":
    db = connect()
    for i, m in enumerate(MIGRATIONS):
        print(f'Applying migration {i}')
        apply(db, m.transform, i)


