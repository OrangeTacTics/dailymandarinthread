import os

from chairmanmao.store.mongodb import MongoDbDocumentStore
from chairmanmao.store.memory import MemoryDocumentStore
from chairmanmao.store import DocumentStore
from chairmanmao.api import Api

from dotenv import load_dotenv

load_dotenv()


def test_create():
    store: DocumentStore = MemoryDocumentStore()

    profiles = store.get_all_profiles()
    assert len(profiles) == 0
    store.create_profile(12345, 'OrangeTacTics#1234')
    profiles = store.get_all_profiles()
    assert len(profiles) == 1


def test_starting_social_credit_yuan():
    store: DocumentStore = MemoryDocumentStore()
    api: Api = Api(store)

    store.create_profile(12345, 'OrangeTacTics#1234')
    assert api.social_credit(12345) == 1000
    assert api.yuan(12345) == 0


def test_honor_dishonor():
    store: DocumentStore = MemoryDocumentStore()
    api: Api = Api(store)

    store.create_profile(12345, 'OrangeTacTics#1234')
    assert api.social_credit(12345) == 1000
    api.honor(12345, 10)
    assert api.social_credit(12345) == 1010
    api.dishonor(12345, 15)
    assert api.social_credit(12345) == 995


def test_mine():
    store: DocumentStore = MemoryDocumentStore()
    api: Api = Api(store)

    store.create_profile(12345, 'OrangeTacTics#1234')
    api.mine(12345, '猫')
    assert api.get_mined(12345) == ['猫']
    api.mine(12345, '狗')
    assert api.get_mined(12345) == sorted(['猫', '狗'])


#    print('Display name:', comrade_api.get_name())
#    comrade_api.set_name('Snick')
#    print('Display name:', comrade_api.get_name())
#    comrade_api.set_name('Snickers')
#    print('Display name:', comrade_api.get_name())
#    print()
#
#    lines = [
#        "The DMT Leaderboard",
#        "```",
#    ]
#    for entry in comrade_api.leaderboard():
#        line = f'{entry.credit} ... {entry.display_name}'
#        lines.append(line)
#
#    lines.append("```")
#    print('\n'.join(lines))
#    print()
#
#    print('Snickers credit:', comrade_api.social_credit(snickers_id))
#    print('dishonor 10...')
#    chairman_api.dishonor(snickers_id, 10)
#    print('Snickers credit:', comrade_api.social_credit(snickers_id))
#    print('honor 11...')
#    chairman_api.honor(snickers_id, 11)
#    print('Snickers credit:', comrade_api.social_credit(snickers_id))
#    print()
#
#    for word in api.as_comrade(snickers_id).get_mined():
#        print('-', word)
#    print()
