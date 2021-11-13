def main():
    from dotenv import load_dotenv
    from dmt_chairmanmao.chairmanmao import ChairmanMao

    load_dotenv()
    chairmanmao = ChairmanMao()
    chairmanmao.run()
