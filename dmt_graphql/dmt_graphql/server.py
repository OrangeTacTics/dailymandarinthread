import typing as t
import jwt
import json
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse, PlainTextResponse, Response

from .graphql.schema import schema
from .graphql.context import ChairmanMaoGraphQL

import os


def make_app() -> t.Any:
    JWT_KEY = t.cast(str, os.getenv("JWT_KEY"))

    app = FastAPI()

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
            request.state.token = jwt.decode(request.cookies["token"], JWT_KEY, algorithms=["HS256"])
        else:
            request.state.token = None

        response = await call_next(request)
        return response

    return app
