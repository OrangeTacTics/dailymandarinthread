from .server import make_app


def main():
    import os
    import uvicorn
    from dotenv import load_dotenv

    load_dotenv()

    uvicorn.run(
        make_app(),
        host=os.environ.get("SERVER_HOST", "0.0.0.0"),
        port=int(os.environ.get("SERVER_PORT", "8004")),
    )
