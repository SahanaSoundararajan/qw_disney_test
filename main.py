import os
import json
import unittest
import logging
import traceback
from autologging import logged, traced

# disabling mock service debug logs
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
# disable Flask default log
os.environ['WERKZEUG_RUN_MAIN'] = 'true'

logging.getLogger("botocore").propagate = False
logging.getLogger("boto3").propagate = False
logging.getLogger("s3transfer").propagate = False
logging.getLogger("urllib3").propagate = False
logging.getLogger("selenium").propagate = False

# disabling mock logs
logging.getLogger("qw_utils.features.api_mock.qube_account").propagate = False

TOKEN_JSON = os.path.abspath('../Admin.json')

API_MIN_ELAPSED_TIME = 3