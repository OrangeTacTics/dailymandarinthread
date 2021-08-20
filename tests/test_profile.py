from chairmanmao.profile import create_profile, get_profile, set_profile
from chairmanmao.hanzi import get_seen_hanzi, see_hanzi


def test_profile_create_get(empty_db):
    db = empty_db

    username = 'OrangeTacTics#0949'
    create_profile(db,  username)
    profile = get_profile(db, username)

    assert profile.username == username
    assert profile.display_name == username
    assert profile.credit == 1000


def test_profile_get_does_not_exist(empty_db):
    db = empty_db

    profile = get_profile(db, 'OrangeTacTics#0949')
    assert profile is None


def test_get_seen_hanzi_empty(empty_db):
    db = empty_db
    assert get_seen_hanzi(db) == set()


def test_see_hanzi_get_seen_hanzi(empty_db):
    db = empty_db

    username = 'OrangeTacTics#0949'
    create_profile(db,  username)

    hanzi = {'我', '爱', '你'}
    see_hanzi(db, username, hanzi)
    assert get_seen_hanzi(db) == hanzi
