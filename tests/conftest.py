import pytest
import pymongo
from dotenv import load_dotenv
import os
import sys

sys.path.append(os.getcwd())


load_dotenv()

MONGODB_TEST_URL = os.getenv('MONGODB_TEST_URL')
MONGODB_TEST_DB = os.getenv('MONGODB_TEST_DB')


@pytest.fixture
def empty_db():
    client = pymongo.MongoClient(MONGODB_TEST_URL)
    assert 'TEST' in MONGODB_TEST_DB, "Cannot delete everything from a database that doesn't have the word 'TEST' in it"
    db = client[MONGODB_TEST_DB]
    db['Profiles'].delete_many({})
    yield db
