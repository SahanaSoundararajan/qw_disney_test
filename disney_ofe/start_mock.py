import qube_account

import logging
from autologging import logged, traced

LOGGER = logging.getLogger(__name__)


@traced
@logged
class StartMock():

    def __init__(self, service = "distributors", results = None):

        self.qubeAccountObj = qube_account.QubeAccountMock(service = service, results = results)