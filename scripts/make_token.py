import sys
import jwt
import os
from dotenv import load_dotenv

load_dotenv()
JWT_KEY = os.environ['JWT_KEY']

username = sys.argv[1]
cookie_json = jwt.encode(
    {
        "username": username,
    },
    JWT_KEY,
    algorithm="HS256",
)

print(cookie_json)
