import typing as t
import jwt
import json
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse, PlainTextResponse

from .graphql.schema import schema
from .graphql.context import ChairmanMaoGraphQL

from dotenv import load_dotenv
import pymongo
import os

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
MONGODB_DB = os.getenv("MONGODB_DB")
CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
JWT_KEY = t.cast(str, os.getenv("JWT_KEY"))
SERVER_HOSTNAME = os.getenv("SERVER_HOSTNAME", "")


client = pymongo.MongoClient(MONGODB_URL)
db = client[MONGODB_DB]

app = FastAPI()

Json = t.Any

graphql_app = ChairmanMaoGraphQL(schema)

app.add_route("/graphql", graphql_app)
app.add_websocket_route("/graphql", graphql_app)


@app.middleware("http")
async def add_graphql_context(request: Request, call_next):
    if "Authorization" in request.headers:
        auth_header = request.headers["Authorization"]
        assert auth_header.startswith("BEARER ")
        token = auth_header[len("BEARER ") :]
        request.state.token = jwt.decode(token, JWT_KEY, algorithms=["HS256"])

    elif "token" in request.cookies:
        request.state.token = jwt.decode(
            request.cookies["token"], JWT_KEY, algorithms=["HS256"]
        )
    else:
        request.state.token = None

    response = await call_next(request)
    return response


async def query_graphql(
    query: str,
    auth_token: t.Optional[str] = None,
    params: t.Dict = {},
) -> t.Any:
    async with httpx.AsyncClient() as client:
        headers = {
            "Content-Type": "application/json",
        }
        if auth_token is not None:
            headers["Authorization"] = f"BEARER {auth_token}"

        payload = {
            "query": query,
            "variables": params,
        }
        resp = await client.post(
            SERVER_HOSTNAME + "/graphql", json=payload, headers=headers
        )
        print(json.dumps(json.loads(resp.text), indent=4))
        print()
        resp.raise_for_status()

    return resp.json()["data"]


@app.get("/profile/{user_id}")
async def route_profile_memberid(
    request: Request,
    response: JSONResponse,
    user_id: str,
):
    auth_token = request.cookies["token"]
    query = """
        query find($userId: String) {
            profile(userId: $userId) {
                userId
                displayName
            }
        }
    """
    params = {
        "userId": user_id,
    }
    data = await query_graphql(query, auth_token, params)

    return PlainTextResponse(content=json.dumps(data, indent=4, ensure_ascii=False))


@app.get("/profile/search/{query_string}")
async def route_profile_search(
    request: Request,
    response: JSONResponse,
    query_string: str,
):
    auth_token = request.cookies["token"]
    query = """
        query find($query: String) {
            findProfile(query: $query) {
                userId
                displayName
            }
        }
    """
    params = {
        "query": query_string,
    }
    data = await query_graphql(query, auth_token, params)
    profile = data["findProfile"]
    if profile is not None:
        user_id = profile["userId"]
        print("Found user_id", user_id)
        return RedirectResponse(f"/profile/{user_id}")
    else:
        return PlainTextResponse(content="User not found")


@app.get("/profile")
async def route_profile(
    request: Request,
    response: JSONResponse,
    code: t.Optional[str] = None,
):
    if request.state.token is None:
        return RedirectResponse("/login")
    else:
        auth_token = request.cookies["token"]
        query = """
            {
                me {
                    userId
                    username
                    displayName
                    credit
                    yuan
                    roles
                    minedWords
                }
            }
        """

        data = await query_graphql(query, auth_token)
        json_str = json.dumps(data, indent=4, ensure_ascii=False)
        return PlainTextResponse(content=json_str)


@app.get("/leaderboard")
async def route_leaderboard():
    query = """
        query leaderboard {
          leaderboard {
            name
            credit
          }
        }
    """

    data = await query_graphql(query)
    json_str = json.dumps(data, indent=4, ensure_ascii=False)
    return PlainTextResponse(content=json_str)


@app.get("/logout")
async def route_logout(response: JSONResponse):
    response.delete_cookie(key="token")
    return "Bye"


async def code_to_access_token(code: str) -> str:
    url = "https://discord.com/api/oauth2/token"

    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "redirect_uri": "https://dailymandarinthread.info/login",
        "code": code,
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    async with httpx.AsyncClient() as client:
        oauth_resp = await client.post(url, data=payload, headers=headers)

    access_token = oauth_resp.json()["access_token"]
    return access_token


async def get_discord_profile(access_token: str) -> Json:
    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://discord.com/api/v9/users/@me", headers=headers
        )
    profile = response.json()
    return profile


@app.get("/login")
async def route_login(request: Request, code: t.Optional[str] = None):
    if request.state.token is not None:
        return RedirectResponse("/profile")

    if code is None:
        redirect_url = "https://discord.com/api/oauth2/authorize?client_id=876378479585808404&redirect_uri=https%3A%2F%2Fdailymandarinthread.info%2Flogin&response_type=code&scope=identify"
        return RedirectResponse(redirect_url)

    else:
        access_token = await code_to_access_token(code)
        profile = await get_discord_profile(access_token)

        username = profile["username"] + "#" + profile["discriminator"]
        cookie_json = jwt.encode(
            {
                "username": username,
            },
            JWT_KEY,
            algorithm="HS256",
        )
        assert isinstance(cookie_json, bytes)

        response = RedirectResponse("/profile")
        response.set_cookie(key="token", value=cookie_json.decode())
        return response
