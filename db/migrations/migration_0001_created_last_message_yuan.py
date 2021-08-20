from datetime import datetime
import pprint
def transform(profile):
    now = datetime.now().replace(microsecond=0)
    profile['memberid'] = None
    profile['created'] = now
    profile['roles'] = []
    profile['last_message'] = now
    profile['yuan'] = 0
    return profile
