import typing as t
from dataclasses import dataclass

from strawberry.asgi import GraphQL
from strawberry.dataloader import DataLoader

from starlette.requests import Request
from starlette.responses import Response
from starlette.websockets import WebSocket

import dmt_graphql.graphql.dataloaders as dl
import dmt_graphql.graphql.schema as schema
from ..store.mongodb import MongoDbDocumentStore
from dmt_graphql.config import Configuration


MemberId = str
DiscordUsername = str


@dataclass
class Dataloaders:
    profile: DataLoader[MemberId, schema.Profile]
    profile_by_discord_username: DataLoader[DiscordUsername, schema.Profile]
    exam: DataLoader[str, schema.Exam]


@dataclass
class Context:
    dataloaders: Dataloaders
    discord_username: t.Optional[str]
    store: MongoDbDocumentStore
    configuration: Configuration

    @property
    def is_admin(self) -> bool:
        if self.discord_username is None:
            return False

        return (
            self.discord_username == self.configuration.ADMIN_USERNAME or self.discord_username == self.configuration.BOT_USERNAME
        )


class ChairmanMaoGraphQL(GraphQL):
    def __init__(self, schema, configuration: Configuration):
        super().__init__(schema)
        self.configuration = configuration

    async def get_context(
        self,
        request: t.Union[Request, WebSocket],
        response: t.Optional[Response] = None,
    ) -> t.Any:
        store = MongoDbDocumentStore(self.configuration)

        if request.state.token is not None:
            discord_username = request.state.token.get("username")
            if discord_username is None:
                discord_username = request.state.token["discordUsername"]
        else:
            discord_username = None

        return Context(
            dataloaders=Dataloaders(
                profile=DataLoader(load_fn=lambda ids: dl.load_profiles(store, ids)),
                profile_by_discord_username=DataLoader(
                    load_fn=lambda duns: dl.load_profiles_by_discord_usernames(store, duns)
                ),
                exam=DataLoader(load_fn=lambda exam_names: dl.load_exams(store, exam_names)),
            ),
            discord_username=discord_username,
            store=store,
            configuration=self.configuration,
        )
