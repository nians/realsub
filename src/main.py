import logging

from src.app import SubtitleApp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(message)s",
    datefmt="%H:%M:%S",
)
# Suppress noisy third-party loggers
logging.getLogger("argostranslate").setLevel(logging.WARNING)
logging.getLogger("stanza").setLevel(logging.WARNING)
logging.getLogger("ctranslate2").setLevel(logging.WARNING)


def main():
    app = SubtitleApp()
    app.run()


if __name__ == "__main__":
    main()
