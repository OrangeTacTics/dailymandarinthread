from .server import make_app
from .graphql.schema import schema


_ = schema


def main():
    import os
    import uvicorn
    from dotenv import load_dotenv

    load_dotenv()

    uvicorn.run(
        make_app(),
        host=os.environ.get("SERVER_HOST", "0.0.0.0"),
        port=int(os.environ.get("SERVER_PORT", "8002")),
    )


def main_test():
    import os
    import uvicorn
    from dotenv import load_dotenv

    load_dotenv()

    os.environ["MONGODB_URL"] = os.environ["MONGODB_TEST_URL"]
    os.environ["MONGODB_DB"] = os.environ["MONGODB_TEST_DB"]

    uvicorn.run(
        make_app(),
        host=os.environ.get("SERVER_HOST", "0.0.0.0"),
        port=int(os.environ.get("SERVER_PORT", "9666")),
        access_log=False,
    )
