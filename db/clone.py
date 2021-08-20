import os
import pymongo
from dotenv import load_dotenv

import db.migrations.migration_0001_created_last_message_yuan as m1

load_dotenv()

MONGODB_URL = os.getenv('MONGODB_URL')
MONGODB_DB = os.getenv('MONGODB_DB')

MONGODB_TEST_URL = os.getenv('MONGODB_TEST_URL')
MONGODB_TEST_DB = os.getenv('MONGODB_TEST_DB')

if __name__ == "__main__":
    assert (MONGODB_URL, MONGODB_DB) != (MONGODB_TEST_URL, MONGODB_TEST_DB)
    src_client = pymongo.MongoClient(MONGODB_URL)
    dst_client = pymongo.MongoClient(MONGODB_TEST_URL)

    src_db = src_client[MONGODB_DB]
    dst_db = dst_client[MONGODB_TEST_DB]

    dst_db['Profiles'].delete_many({})
    for record in src_db['Profiles'].find({}):
        print('Copying profile', record['_id'])
        dst_db['Profiles'].insert_one(record)
