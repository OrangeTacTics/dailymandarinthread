import json
import sys
import os

from dotenv import load_dotenv
from server.store.mongodb import MongoDbDocumentStore
from server.store.types import Exam, Question

load_dotenv()

exam_filepath = sys.argv[1]

MONGODB_URL = os.getenv("MONGODB_URL", "")
MONGODB_DB = os.getenv("MONGODB_DB", "")

store = MongoDbDocumentStore(MONGODB_URL, MONGODB_DB)

with open(exam_filepath) as infile:
    json_data = json.load(infile)


cards = []
for card in json_data['cards']:
    cards.append(
        Question(
            question=card['question'],
            valid_answers=card['valid_answers'],
            meaning=card['meaning'],
        )
    )

exam = Exam(
    name=json_data['name'],
    hsk_level=json_data['hsk_level'],
    max_wrong=json_data['max_wrong'],
    num_questions=json_data['num_questions'],
    timelimit=json_data['timelimit'],
    deck=cards,
)

exam = store.store_exam(exam)
