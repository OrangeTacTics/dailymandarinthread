import os

from dotenv import load_dotenv

from chairmanmao.chairmanmao import client


if __name__ == '__main__':
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
    client.run(TOKEN)
