import logging
import os
import sys

logger=logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter=logging.Formatter('%(asctime)s-%(levelname)s-%(message)s')
handler=logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)

DATABASE_URL=os.environ.get('DATABASE_URL')


if not DATABASE_URL:
    logger.critical("No database URL available")
    sys.exit(1)