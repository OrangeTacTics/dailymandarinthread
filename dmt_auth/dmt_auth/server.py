import typing as t
import jwt
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse

import os


def make_app() -> t.Any:
    JWT_KEY = t.cast(str, os.getenv("JWT_KEY"))

    app = FastAPI()

    @app.get("/login")
    async def route_login(request: Request, code: t.Optional[str] = None):
        if hasattr(request.state, 'token') and request.state.token is not None:
            return RedirectResponse("/")

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

            response = RedirectResponse("/")
            response.set_cookie(key="token", value=cookie_json.decode())
            return response

    @app.get("/logout")
    async def route_logout():
        response = RedirectResponse("/")
        response.delete_cookie(key="token")
        return response

    return app


async def code_to_access_token(code: str) -> str:
    CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
    CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
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


async def get_discord_profile(access_token: str) -> t.Any:
    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get("https://discord.com/api/v9/users/@me", headers=headers)

    profile = response.json()
    return profile
