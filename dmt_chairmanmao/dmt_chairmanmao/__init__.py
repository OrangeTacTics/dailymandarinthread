def main():
    from dmt_chairmanmao.chairmanmao import ChairmanMao
    from .config import Configuration

    config = Configuration.from_environment()
    chairmanmao = ChairmanMao(config)
    chairmanmao.run()
