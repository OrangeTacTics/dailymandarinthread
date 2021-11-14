from __future__ import annotations
from dataclasses import dataclass
import os


@dataclass
class Configuration:
    DISCORD_TOKEN: str
    GRAPHQL_ENDPOINT: str
    GRAPHQL_TOKEN: str
    DO_SPACES_KEY: str
    DO_SPACES_SECRET: str
    DO_SPACES_BUCKETNAME: str
    DO_SPACES_URL: str
    DO_SPACES_REGION: str
    BOT_USERNAME: str

    @staticmethod
    def from_environment() -> Configuration:
        from dotenv import load_dotenv
        load_dotenv()

        return Configuration(
            DISCORD_TOKEN=os.environ["DISCORD_TOKEN"],
            GRAPHQL_ENDPOINT=os.environ["GRAPHQL_ENDPOINT"],
            GRAPHQL_TOKEN=os.environ["GRAPHQL_TOKEN"],
            DO_SPACES_KEY=os.environ["DO_SPACES_KEY"],
            DO_SPACES_SECRET=os.environ["DO_SPACES_SECRET"],
            DO_SPACES_BUCKETNAME=os.environ["DO_SPACES_BUCKETNAME"],
            DO_SPACES_URL=os.environ["DO_SPACES_URL"],
            DO_SPACES_REGION=os.environ["DO_SPACES_REGION"],
            BOT_USERNAME=os.environ["BOT_USERNAME"],
        )
