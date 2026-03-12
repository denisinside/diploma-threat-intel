import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from loguru import logger

from broker.consumer import run_consumer


def main() -> None:
    logger.info("Starting notification-service...")
    run_consumer()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("notification-service interrupted by user")
