from .config import Config
from .loop import Loop


def main():
    config = Config.from_env()
    loop = Loop(config=config)
    try:
        loop.start()
        loop.join()
    except KeyboardInterrupt:
        loop.stop()
        loop.join()
    finally:
        print("Exiting...")


if __name__ == "__main__":
    main()
