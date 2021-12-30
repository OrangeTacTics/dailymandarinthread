from __future__ import annotations
from dataclasses import dataclass
import os


@dataclass
class Configuration:
    MONGODB_URL: str
    MONGODB_DB: str
    MONGODB_USER: str
    MONGODB_PASS: str
    MONGODB_CERT: str
    JWT_KEY: str
    ADMIN_USERNAME: str
    BOT_USERNAME: str

    @staticmethod
    def from_environment() -> Configuration:
        from dotenv import load_dotenv

        load_dotenv()

        return Configuration(
            MONGODB_URL=os.environ["MONGODB_URL"],
            MONGODB_DB=os.environ["MONGODB_DB"],
            MONGODB_USER=os.environ["MONGODB_USER"],
            MONGODB_PASS=os.environ["MONGODB_PASS"],
            MONGODB_CERT=os.environ["MONGODB_CERT"],
            JWT_KEY=os.environ["JWT_KEY"],
            ADMIN_USERNAME=os.environ["ADMIN_USERNAME"],
            BOT_USERNAME=os.environ["BOT_USERNAME"],
        )
