import os
import uvicorn
from dotenv import load_dotenv
from chairmanmao.chairmanmao import ChairmanMao
from chairmanmao.server import app


def bot():
    load_dotenv()
    chairmanmao = ChairmanMao()
    chairmanmao.run()


def server():
    load_dotenv()

    uvicorn.run(
        app,
        host=os.environ.get("SERVER_HOST", "127.0.0.1"),
        port=int(os.environ.get("SERVER_PORT", "8002")),
    )
