import json
import psycopg2
import logging
from autologging import traced, logged
import config

TWO_FACTOR_AUTH_SMS_HASH = '$2a$10$NERAvQcFfCerjZTtHLJDUOU8DLeuy3jTvdYadLjONxSZ1hnSzG8rq'

LOGGER = logging.getLogger(__name__)

@logged
@traced
class Db():

    def __init__(self, results = None):
        """
        Constructor
        :param dbHost: (str) DB Url
        :param dbName: (str) DB name
        :param dbUserName: (str) user name
        :param dbPassword: (str) password
        :param results: (str) result object
        """

        self.results = results
        if self.results is None:
            self.results = {"resultAttachments": {}, "output": "", "executedWithWarnings": False}

        self.config = config.Config(service = 'qubeaccount')
        dbDetails = "dbname={0} user={1} host={2} password={3} ".format(self.config.dbName, self.config.dbUsername,
                                                                        self.config.dbHost, self.config.dbPassword)
        self.connection = psycopg2.connect(dbDetails)
        self.cursor = self.connection.cursor()

    def __del__(self):

        self.cursor.close()
        self.connection.close()

    def getAuthCodeToken(self, email, clientId, productId):
        """
        """

        selectAuthCode = "select oauth_access_tokens.token, oauth_access_tokens.company_id, oauth_access_tokens.refresh_token, " \
                           "oauth_access_tokens.scope, oauth_access_tokens.expires_on from oauth_access_tokens LEFT JOIN users ON" \
                           " oauth_access_tokens.user_id = users.id LEFT JOIN oauth_clients ON oauth_access_tokens.client_id = oauth_clients.id" \
                           " where users.email = '{0}' and oauth_access_tokens.product_id = '{1}' and oauth_clients.client_id = '{2}' order by" \
                           " issued_on DESC".format(email, productId, clientId)

        self.cursor.execute(selectAuthCode)
        res = self.cursor.fetchone()

        if not res or len(res) is not 5:
            raise Exception("No auth code found for the user: {0}".format(email))

        result = {'access_token' : res[0], 'company_id' : res[1], 'refresh_token' : res[2], 'scopes' : res[3],
                  'expires_in' : 0, 'token_type' : 'Bearer', 'username' : email, 'product_id' : productId}
        LOGGER.debug('AuthCode from DB: {0}'.format(result))
        return result

    def updateOtpHash(self, challengeId):

        getJsonObj = "select code from login_challenges where id = '{challengeId}'".format(challengeId = challengeId)

        self.cursor.execute(getJsonObj)

        res = self.cursor.fetchone()
        res[0]['0']['sms']['code'] = TWO_FACTOR_AUTH_SMS_HASH

        updateSmsOtpHashCode = "UPDATE login_challenges set code = '{updateJsonObj}' where id = '{challengeId}'".\
            format(updateJsonObj = json.dumps(res[0]), challengeId = challengeId)

        self.cursor.execute(updateSmsOtpHashCode)

        self.connection.commit()