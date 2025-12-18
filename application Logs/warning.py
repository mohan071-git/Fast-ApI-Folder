import logging
import os
import sys

logger=logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter=logging.Formatter('%(asctime)s-%(levelname)s-%(message)s')
handler=logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)

import telnetlib
logger.warning('talnetlib is deprecated')
