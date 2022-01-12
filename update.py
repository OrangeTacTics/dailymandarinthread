from redis import Redis
import os

os.system('mkdir -p emoji')

redis = Redis()
redis.set('syncbot:users', open('users.json').read().encode())
redis.set('syncbot:roles', open('roles.json').read().encode())
redis.set('syncbot:emojis', open('emojis.json').read().encode())
