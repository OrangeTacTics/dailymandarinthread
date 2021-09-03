from datetime import datetime
import pprint
def transform(profile):
    if '#' in profile['display_name']:
        assert profile['display_name'][-5] == '#'
        profile['display_name'] = profile['display_name'][:-5]
        assert '#' not in profile['display_name']

    return profile
