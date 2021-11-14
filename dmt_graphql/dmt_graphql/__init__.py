from .server import make_app
from .graphql.schema import schema


_ = schema


def main():
    import uvicorn

    uvicorn.run(
        make_app(),
        host="0.0.0.0",
        port=8002,
    )
