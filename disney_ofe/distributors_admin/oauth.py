import logging
from autologging import traced, logged
import config 
from qubeaccount import oauth

LOGGER = logging.getLogger(__name__)


@traced
@logged
class OAuth(oauth.OAuth):

    def __init__(self, tokenJsonFile, userAccount, oauthType = "AuthCode", clientId = None, clientSecret = None,
                 productId = None, clientRedirectUrl = None, browser = "chrome", results = None, useMock = True):

        self.results = results
        if results is None:
            self.results = {"resultAttachments": {}, "output": "", "executedWithWarnings": False}

        self.config = config.Config(service = "distributors_admin")
        self.oauthObj = oauth.OAuth(browser = browser, results = self.results)

        self.clientId = clientId if clientId else self.config.clientId
        self.clientSecret = clientSecret if clientSecret else self.config.clientSecret
        self.productId = productId if productId else self.config.productId
        self.clientRedirectUrl = clientRedirectUrl if clientRedirectUrl else self.config.clientRedirectUrl

        userAccount = getattr(self.config, str(userAccount), userAccount)
        self.qubeAccountEmail = userAccount["qubeAccountEmail"]
        self.qubeAccountPassword = userAccount["qubeAccountPassword"]
        self.email = userAccount.get("email")
        self.password = userAccount.get("password")

        self.token = userAccount.get("token")

        if not useMock:
            if oauthType.lower() == "authcode":
                self.token = self.oauthObj.getAuthCodeToken(qubeAccountUsername = self.qubeAccountEmail,
                                                            qubeAccountPassword = self.qubeAccountPassword,
                                                            clientId = self.clientId, clientSecret = self.clientSecret,
                                                            productId = self.productId,
                                                            redirectUri = self.clientRedirectUrl,
                                                            tokenJsonFile = tokenJsonFile,
                                                            email = self.email, password = self.password)
            elif oauthType.lower() == "polling":
                self.token = self.oauthObj.getPollingToken(qubeAccountUsername = self.qubeAccountEmail,
                                                           qubeAccountPassword = self.qubeAccountPassword,
                                                           clientId = self.clientId, clientSecret = self.clientSecret,
                                                           productId = self.productId, tokenJsonFile = tokenJsonFile,
                                                           email = self.email, password = self.password)
            else:
                raise Exception("Invalid oauthType: '{0}'".format(oauthType))