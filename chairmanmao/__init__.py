def main():
    from dotenv import load_dotenv
    from chairmanmao.chairmanmao import ChairmanMao

    load_dotenv()
    chairmanmao = ChairmanMao()
    chairmanmao.run()
