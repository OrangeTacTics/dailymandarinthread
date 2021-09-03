from datetime import datetime
import pprint
def transform(profile):
    if 'mined_words' not in profile:
        profile['mined_words'] = []

    return profile
