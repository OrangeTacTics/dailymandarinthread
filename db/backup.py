from datetime import datetime
import json
import os
from pathlib import Path

import pymongo
from dotenv import load_dotenv

from chairmanmao.profile import profile_from_json


load_dotenv()

MONGODB_URL = os.getenv('MONGODB_URL')
MONGODB_DB = os.getenv('MONGODB_DB')


if __name__ == "__main__":
    backup_dir = Path('db/backups')
    backup_dir.mkdir(exist_ok=True)

    client = pymongo.MongoClient(MONGODB_URL)
    db = client[MONGODB_DB]

    now = str(datetime.now().replace(microsecond=0))
    now = now.replace(' ', '_').replace(':', '_').replace('-', '_')
    date_dir = backup_dir / f'{now}'
    date_dir.mkdir()

    records = []
    to_str_fields = ['_id', 'last_message', 'created']
    for record in db['Profiles'].find({}):
        for field in to_str_fields:
            record[field] = str(record[field])
        records.append(record)

    profiles_filepath = date_dir / 'Profiles.json'
    print('Saving Profiles:', profiles_filepath)
    with open(profiles_filepath, 'w') as outfile:
        json.dump(records, outfile, ensure_ascii=False, indent=4)
