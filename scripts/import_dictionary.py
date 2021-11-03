import sys
import os

from dotenv import load_dotenv
from server.store.mongodb import MongoDbDocumentStore
from server.store.types import DictEntry

load_dotenv()

dict_path = sys.argv[1]

MONGODB_URL = os.getenv("MONGODB_URL", "")
MONGODB_DB = os.getenv("MONGODB_DB", "")

store = MongoDbDocumentStore(MONGODB_URL, MONGODB_DB)


store.dict_entries.delete_many({})

def parse_dictentry(line: str) -> DictEntry:
    traditional, simplified, *_ = line.split(" ")
    left_brace = line.index("[")
    right_brace = line.index("]")
    pinyin_numbered = line[left_brace + 1 : right_brace]

    slash = line.index("/")
    meanings = []
    try:
        while True:
            line = line[slash + 1 :]
            slash = line.index("/")
            meaning = line[:slash]
            meanings.append(meaning)
    except:
        pass

    return {
        'simplified': simplified,
        'traditional': traditional,
        'pinyin': pinyin_numbered,
        'meanings': meanings,
    }


dict_entries = []
with open(dict_path) as infile:
    for line in infile:
        if line.startswith("#"):
            continue
        dict_entries.append(parse_dictentry(line))

result = store.dict_entries.insert_many(dict_entries)
print(len(result.inserted_ids))
