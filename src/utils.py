from typing import Union
import os
import logging
from datetime import datetime

from dotenv import load_dotenv


def setup_logging():
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(logs_dir, exist_ok=True)

    # Create log filename with current timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_file = os.path.join(logs_dir, f'{timestamp}.log')

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('discord_deletion_tool')


def get_authorization_token(token_name: str) -> Union[str, None]:
    load_dotenv()
    logger = logging.getLogger('discord_deletion_tool')
    result = os.getenv(token_name)
    if result:
        logger.info('Successfully retrieved Discord token from env')
    else:
        logger.error('Failed to retrieve Discord token from environment')
    return result
