import logging

logger = logging.getLogger(__name__)


def execute():
    logger.info("Executing")
    print("Hello from {{ package_name }}")