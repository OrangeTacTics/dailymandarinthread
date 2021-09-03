import os
import pymongo
from dotenv import load_dotenv

import db.migrations.migration_0000_objectids_not_memberids as m0000
import db.migrations.migration_0001_created_last_message_yuan as m0001
import db.migrations.migration_0002_strip_discriminator_from_displayname as m0002
import db.migrations.migration_0003_add_mined as m0003

load_dotenv()

################################################################################
# vvvvvv DANGER!
################################################################################

if os.getenv('MIGRATE_PRODUCTION') == 'True':
    MIGRATE_PRODUCION = True
elif os.getenv('MIGRATE_PRODUCTION') == 'False':
    MIGRATE_PRODUCION = False
else:
    raise Exception('Environment variable MIGRATE_PRODUCTION must be set to "True" or "False"')

################################################################################
# ^^^^^^ DANGER!
################################################################################

if MIGRATE_PRODUCION:
    MONGODB_URL = os.getenv('MONGODB_URL')
    MONGODB_DB = os.getenv('MONGODB_DB')
else:
    MONGODB_URL = os.getenv('MONGODB_TEST_URL')
    MONGODB_DB = os.getenv('MONGODB_TEST_DB')


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
    m0002,
    m0003,
]

if __name__ == "__main__":
    db = connect()
    for i, m in enumerate(MIGRATIONS):
        print(f'Applying migration {i}')
        apply(db, m.transform, i)


