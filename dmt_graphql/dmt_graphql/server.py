import typing as t
import jwt
from fastapi import FastAPI, Request

from .graphql.schema import schema
from .graphql.context import ChairmanMaoGraphQL
from .config import Configuration


def make_app() -> t.Any:
    configuration = Configuration.from_environment()

    app = FastAPI()

    graphql_app = ChairmanMaoGraphQL(schema, configuration)

    app.add_route("/graphql", graphql_app)
    app.add_websocket_route("/graphql", graphql_app)

    @app.middleware("http")
    async def add_graphql_context(request: Request, call_next):
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            assert auth_header.startswith("BEARER ")
            token = auth_header[len("BEARER ") :]
            request.state.token = jwt.decode(token, configuration.JWT_KEY, algorithms=["HS256"])
        elif "token" in request.cookies:
            request.state.token = jwt.decode(request.cookies["token"], configuration.JWT_KEY, algorithms=["HS256"])
        else:
            request.state.token = None

        response = await call_next(request)
        return response

    return app
