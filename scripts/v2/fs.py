import logging
import os

logger = logging.getLogger('datahub_docker_stacks')

ARTIFACTS_PATH = 'artifacts'

def store(filename: str, formatted_data: str, filepath: str = ARTIFACTS_PATH) -> bool:
    try:
        with open(os.path.join(filepath, filename), 'w') as f:
            f.write(formatted_data)

        return True
    except Exception as e:
        logger.error(e)
        return False
