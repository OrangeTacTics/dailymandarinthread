import json
import sys
import os

from dotenv import load_dotenv
from server.store.mongodb import MongoDbDocumentStore
from server.store.types import Exam

load_dotenv()

exam_name = sys.argv[1]

MONGODB_URL = os.getenv("MONGODB_URL", "")
MONGODB_DB = os.getenv("MONGODB_DB", "")

store = MongoDbDocumentStore(MONGODB_URL, MONGODB_DB)
exam = store.load_exam(exam_name)

cards = []
for card in exam.deck:
    cards.append({
        'question': card.question,
        'valid_answers': card.valid_answers,
        'meaning': card.meaning,
    })

json_data = {
    'name': exam.name,
    'hsk_level': exam.hsk_level,
    'max_wrong': exam.max_wrong,
    'name': exam.name,
    'num_questions': exam.num_questions,
    'timelimit': exam.timelimit,
    'cards': cards,
}

print(json.dumps(json_data, indent=4, ensure_ascii=False))
