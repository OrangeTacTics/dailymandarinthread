def main():
    import os
    import uvicorn
    from dotenv import load_dotenv
    from .server import app

    load_dotenv()

    uvicorn.run(
        app,
        host=os.environ.get("SERVER_HOST", "127.0.0.1"),
        port=int(os.environ.get("SERVER_PORT", "8002")),
    )