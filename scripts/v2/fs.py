import logging

logger = logging.getLogger('datahub_docker_stacks')

ARTIFACTS_PATH = 'artifacts'
MANIFEST_PATH = 'manifests'

def store(filepath: str, formatted_data: str) -> bool:
    try:
        with open(filepath, 'w') as f:
            f.write(formatted_data)

        return True
    except Exception as e:
        logger.error(e)
        return False
