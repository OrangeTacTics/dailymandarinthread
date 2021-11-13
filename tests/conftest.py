import requests
import time
import subprocess
import os
import sys
import asyncio

import pytest
import pymongo
from dotenv import load_dotenv

from chairmanmao.api import Api


load_dotenv()


MONGODB_TEST_URL = os.getenv('MONGODB_TEST_URL')
MONGODB_TEST_DB = os.getenv('MONGODB_TEST_DB')


@pytest.fixture(scope="session")
def test_server(request):
    proc = subprocess.Popen(
        [
            'poetry',
            'run',
            'server-testing',
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    ready = False
    start = time.time()
    while not ready:
        try:
            resp = requests.get('http://localhost:9666/graphql')
            if resp.status_code == 200:
                break
        except:
            pass

        time.sleep(1.)
        now = time.time()
        duration = ready - now
        if duration > 10:
            raise Exception('Could not connect to development server.')

    def finalizer():
        proc.terminate()
        proc.wait()

    request.addfinalizer(finalizer)


@pytest.fixture
def empty_db(test_server):
    client = pymongo.MongoClient(MONGODB_TEST_URL)
    assert 'TEST' in MONGODB_TEST_DB, "Cannot delete everything from a database that doesn't have the word 'TEST' in it"
    db = client[MONGODB_TEST_DB]
    db['Profiles'].delete_many({})
    # db['Exams']
    # db['ServerSettings']
    yield db


@pytest.fixture
def api(test_server):
    GRAPHQL_ENDPOINT = 'http://localhost:9666/graphql'
    GRAPHQL_TOKEN = os.getenv("GRAPHQL_TOKEN", "")
    api = Api(GRAPHQL_ENDPOINT, GRAPHQL_TOKEN)
    return api


async def add_three_users(api):
    await api.register(
        user_id="888950825970462730",
        discord_username="ChairmanMao#7877",
    )
    await api.register(
        user_id=182370676877819904,
        discord_username='OrangeTacTics#0949',
    )
    await api.register(
        user_id="878851905021947924",
        discord_username="Snickers#0486",
    )


@pytest.fixture
def three_user_db(empty_db, api):
    db = empty_db
    asyncio.run(add_three_users(api))
    yield db
