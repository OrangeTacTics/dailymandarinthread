import typing as t
from dataclasses import dataclass
import os

from strawberry.types import Info
from strawberry.asgi import GraphQL
from strawberry.dataloader import DataLoader

from starlette.requests import Request
from starlette.responses import Response
from starlette.websockets import WebSocket

import chairmanmao.graphql.dataloaders as dl
import chairmanmao.graphql.schema as schema
from chairmanmao.api import Api
from chairmanmao.store.mongodb import MongoDbDocumentStore


MemberId = str
DiscordUsername = str


@dataclass
class Dataloaders:
    profile: DataLoader[MemberId, schema.Profile]
    profile_by_discord_username: DataLoader[DiscordUsername, schema.Profile]


@dataclass
class Context:
    dataloaders: Dataloaders
    api: Api
    discord_username: t.Optional[str]

    @property
    def is_admin(self) -> bool:
        return self.discord_username is not None and self.discord_username == os.environ['ADMIN_USERNAME']


class ChairmanMaoGraphQL(GraphQL):
    async def get_context(
        self,
        request: t.Union[Request, WebSocket],
        response: t.Optional[Response] = None,
    ) -> t.Any:
        MONGODB_URL = os.getenv('MONGODB_URL', '')
        MONGODB_DB = os.getenv('MONGODB_DB', '')

        store = MongoDbDocumentStore(MONGODB_URL, MONGODB_DB)
        api = Api(store)

        if request.state.token is not None:
            discord_username = request.state.token['username']
        else:
            discord_username = None

        return Context(
            dataloaders=Dataloaders(
                profile=DataLoader(load_fn=lambda ids: dl.load_profiles(store, ids)),
                profile_by_discord_username=DataLoader(load_fn=lambda duns: dl.load_profiles_by_discord_usernames(store, duns)),
            ),
            api=api,
            discord_username=discord_username,
        )
