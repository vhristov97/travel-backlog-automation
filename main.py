import config
from bot import create_app
from logging_setup import setup_logging


def main():
    setup_logging()
    config.validate()
    app = create_app()
    app.run_polling()


if __name__ == "__main__":
    main()
