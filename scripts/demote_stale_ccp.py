import os
from datetime import datetime, timezone

from chairmanmao.api import Api
from chairmanmao.types import Role

from dotenv import load_dotenv


def since_seen(user_id, now, comrade_api):
    last_seen = comrade_api.last_seen(user_id)
    last_seen = last_seen.replace(tzinfo=timezone.utc)
    havent_seen_in = now - last_seen
    return int(havent_seen_in.total_seconds())


def pretty(seconds):
    minutes = seconds // 60
    hours = minutes // 60
    days = hours // 24

    if minutes < 1:
        return f'{seconds} seconds'
    elif hours < 1:
        return f'{minutes} minutes'
    elif days < 1:
        return f'{hours} hours'
    else:
        return f'{days} days'


if __name__ == '__main__':
    load_dotenv()

    MONGODB_URL = os.getenv('MONGODB_URL', '')
    MONGODB_DB = os.getenv('MONGODB_DB', '')
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', '')

    api = Api.connect(MONGODB_URL, MONGODB_DB)
    comrade_api = api.as_comrade(ADMIN_USERNAME)
    chairman_api = api.as_chairman()

    user_ids = chairman_api.list_users()
    now = datetime.now(timezone.utc).replace(microsecond=0)
    last_seens = [(since_seen(user_id, now, comrade_api), user_id) for user_id in user_ids]

    print('Demoting:')
    for last_seen, user_id in sorted(last_seens):
        profile = chairman_api.get_profile(user_id)
        if Role.Party in profile.roles:
            days_since_last_seen = last_seen // 60 // 60 // 24
            if days_since_last_seen > 21:
                print('   ', str(days_since_last_seen).ljust(5), comrade_api.get_discord_username(user_id))
                chairman_api.demote(user_id)

