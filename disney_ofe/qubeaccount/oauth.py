import logging
import traceback
from autologging import traced, logged
import os
import json
import qubeaccount.db
import qubeaccount.login
import utils.RiUtils
import config
import utils.restest

LOGGER = logging.getLogger(__name__)

@logged
@traced
class Api():

    def __init__(self, url, results = None):

        if results is None:
            self.results = {"resultAttachments": {}, "output": "", "executedWithWarnings": False}
        else:
            self.results = results

        self.url = url

    def initialize(self, clientId, productId, raiseForStatus = True, expectedOutput = None):

        requestJson = {"client_id": clientId, "services": productId}
        restTestObj = restest.Restest(method = 'POST', serverUrl = self.url, endpointPath = '/dialog/polling/initialize',
                                      json = requestJson, raiseForStatus = raiseForStatus, expectedOutput = expectedOutput)

        if restTestObj.hasWarnings:
            self.results['executedWithWarnings'] = True

        return restTestObj.response.json()

    def polling(self, pollingUrl, code, clientId, clientSecret, grantType = "authorization_code",
                accessType = "offline", raiseForStatus = True, expectedOutput = None):

        requestJson = {"client_id": clientId, "grant_type": grantType, "client_secret": clientSecret,
                       "access_type": accessType, "code": code}

        restTestObj = restest.Restest(method = 'POST', serverUrl = self.url, endpointPath = pollingUrl,
                                      data = requestJson, raiseForStatus = raiseForStatus,
                                      headers = {'Content-Type': 'application/x-www-form-urlencoded'},
                                      expectedOutput = expectedOutput)

        if restTestObj.hasWarnings:
            self.results['executedWithWarnings'] = True

        return restTestObj.response.json()

    def getTokenInfo(self, token = None, raiseForStatus = True, expectedOutput = None):

        restTestObj = restest.Restest(method = 'GET', serverUrl = self.url, endpointPath = '/api/tokeninfo',
                                      params = {'access_token': token}, raiseForStatus = raiseForStatus,
                                      expectedOutput = expectedOutput)

        if restTestObj.hasWarnings:
            self.results['executedWithWarnings'] = True

        return restTestObj.response.json()

    def refreshToken(self, refreshToken = None, grantType = 'refresh_token', clientId = None, productId = None,
                     clientSecret = None, raiseForStatus = True, expectedOutput = None):

        requestJson = {}
        if refreshToken is not None:
            requestJson.update({"refresh_token": refreshToken})
        if grantType is not None:
            requestJson.update({"grant_type": grantType})
        if clientId is not None:
            requestJson.update({"client_id": clientId})
        if clientSecret is not None:
            requestJson.update({"client_secret": clientSecret})
        if productId is not None:
            requestJson.update({"product_id": productId})

        restTestObj = restest.Restest(method = 'POST', serverUrl = self.url, endpointPath = "/oauth/token",
                                      json = requestJson, raiseForStatus = raiseForStatus,
                                      expectedOutput = expectedOutput)

        if restTestObj.hasWarnings:
            self.results['executedWithWarnings'] = True

        return restTestObj.response.json()

@logged
@traced
class OAuth():

    def __init__(self, browser = 'chrome', results = None):

        self.results = results
        if results is None:
            self.results = {"resultAttachments": {}, "output": "", "executedWithWarnings": False}

        self.config = config.Config(service = "qubeaccount")
        self.url = self.config.url
        self.browser = browser
        self.api = Api(url = self.url, results = self.results)

    def writeToFile(self, fullFilePath, fileContent):
        """
        """

        fileName = os.path.basename(fullFilePath)
        folderPath = os.path.dirname(fullFilePath)

        if not folderPath:
            filePath = fileName
        else:
            if not os.path.exists(folderPath):
                os.makedirs(folderPath)
            filePath = os.path.join(folderPath, fileName)

        with open(filePath, 'w') as f:
            json.dump(fileContent, f)

    def refreshTokenIfExpired(self, token, tokenJsonFile = None):
        """
        refreshTokenIfExpired - refresh the token if it's expired
        :param token: (str) token. The parameter token should be in the form of "<token_type> <access_token>"
        :param tokenJsonFile: token json absolute path
        :return: (str) valid token
        """

        newToken = '{0}'.format(token)
        if not self.isTokenValid(token = token):
            newToken = self.refreshToken(token = token, tokenJsonFile = tokenJsonFile)

        return newToken

    def refreshToken(self, refreshtoken = None, clientId = None, clientSecret = None,
                     productId = None, token = None, tokenJsonFile = None):
        """
        refreshToken
        :param token: (str) token. If this is not given, refreshtoken, clientId, clientSecret, productId has to be given
        :param tokenJsonFile: (str) tokenJsonFile absolute path
        :param refreshtoken: (str) refresh token
        :param clientId: (str) client id
        :param clientSecret: (str) client secret
        :param productId: (str) product id
        :return:
            (str) token if token arg is given
            (refreshToken response object) if refreshToken is given
        """

        if tokenJsonFile is not None and os.path.isfile(tokenJsonFile):
            with open(tokenJsonFile) as fp:
                data = json.load(fp)

            jsonData = list(filter(lambda tokenObj: tokenObj['access_token'] == token.replace('Bearer ', ''), data))

            if jsonData:
                tokenDict = jsonData[0]
                clientId = tokenDict['client_id']
                refreshtoken = tokenDict['refresh_token']
                clientSecret = tokenDict['client_secret']
                productId = tokenDict['product_id']
                accessTokenResponse = self.api.refreshToken(refreshToken = refreshtoken, clientId = clientId,
                                                            clientSecret = clientSecret, productId = productId)

                data.remove(tokenDict)
                tokenDict['access_token'] = accessTokenResponse['access_token']
                tokenDict['expires_in'] = accessTokenResponse['expires_in']
                data.append(tokenDict)

                self.writeToFile(fullFilePath = tokenJsonFile, fileContent = data)
                LOGGER.debug("Token refreshed and updated new token in json file...")
                return '{} {}'.format(accessTokenResponse['token_type'], accessTokenResponse['access_token'])

            LOGGER.error("Token {0} not found in json file".format(token))
            raise Exception("Token '{0}' not found in json file".format(token))
        else:
            LOGGER.warning("json file not found...")
            return self.api.refreshToken(refreshToken = refreshtoken, clientId = clientId,
                                         clientSecret = clientSecret, productId = productId)

    def isTokenValid(self, token):

        try:
            self.api.getTokenInfo(token = token)

            if tokenInfo['expires_in'] <= 15:
                LOGGER.debug("Token {token} is about to expire in {expiresIn} secs so invalidating token".
                              format(token = token, expiresIn = tokenInfo['response']['expiresIn']))
                return False
            return True
        except:
            LOGGER.debug("Token is not valid")
            return False

    def writeTokenToJson(self, tokenDict, tokenJsonFile):

        if tokenJsonFile is not None:
            jsonData = []
            if os.path.isfile(tokenJsonFile):
                with open(tokenJsonFile) as fp:
                    jsonData = json.load(fp)
                userInfoList = filter(lambda userInfo: userInfo['username'] == tokenDict['username'] and \
                                                       userInfo['client_id'] == tokenDict['client_id'], jsonData)
                for userInfo in userInfoList:
                    jsonData.remove(userInfo)

            jsonData.append(tokenDict)
            self.writeToFile(fullFilePath = tokenJsonFile, fileContent = jsonData)

    # def getTokenByUser(self, username, clientId, tokenJsonFile, refreshExpiredToken = True):
    #
    #     if tokenJsonFile is not None and os.path.isfile(tokenJsonFile):
    #         with open(tokenJsonFile) as fp:
    #             jsonData = json.load(fp)
    #         userInfoList = []
    #
    #         for item in jsonData:
    #             if item['username'] == username:
    #                 userInfoList.append(item)
    #
    #         for item in userInfoList:
    #             if item['client_id'] == clientId:
    #                 if refreshExpiredToken:
    #                     return self.refreshTokenIfExpired(token = '{} {}'.format(item['token_type'], item['access_token']))
    #                 else:
    #                     return '{} {}'.format(item['token_type'], item['access_token'])
    #
    #         error = "Token not found for the user: {userId} & client: {clientId}".format(userId = username, clientId = clientId)
    #         LOGGER.error(error)
    #         raise Exception(error)
    #     else:
    #         LOGGER.error(str(tokenJsonFile) + " file not found")
    #         raise Exception(str(tokenJsonFile) + " file not found")

    def getPollingToken(self, qubeAccountUsername, qubeAccountPassword, email, password, clientId, clientSecret,
                        productId, tokenJsonFile, refreshFailedToken = True):

        self.login = login.Login(browser = self.browser, results = self.results)

        if tokenJsonFile is not None and os.path.isfile(tokenJsonFile):
            with open(tokenJsonFile) as fp:
                jsonData = json.load(fp)

            userInfoList = list(filter(lambda userInfo: userInfo['username'] == qubeAccountUsername and \
                                                        userInfo['client_id'] == clientId, jsonData))

            if userInfoList and refreshFailedToken:
                try:
                    token = self.refreshToken(token = userInfoList[0]['access_token'], tokenJsonFile = tokenJsonFile)
                    LOGGER.debug("Access Token returned: '{0}'".format(token))
                    return token
                except Exception as e:
                    LOGGER.debug("Exception in getPollingToken-refreshToken: {e}", e)

        pollingResponse = self.api.initialize(clientId = clientId, productId = productId)
        pollingUrl = pollingResponse['polling_url']
        code = pollingResponse['code']

        self.login.login(qubeAccountUsername = qubeAccountUsername, qubeAccountPassword = qubeAccountPassword,
                         email = email, password = password, code = pollingResponse['code'], isTrustedClient = False)

        pollingTokenList = self.api.polling(pollingUrl = pollingUrl, code = code, clientId = clientId,
                                            clientSecret = clientSecret)

        refreshToken = pollingTokenList[0]['refresh_token']
        accessTokenResponse = self.api.refreshToken(refreshToken = refreshToken, productId = productId,
                                                    clientId = clientId, clientSecret = clientSecret)

        pollingTokenDict = {}
        if accessTokenResponse:
            pollingTokenDict = accessTokenResponse
            pollingTokenDict['refresh_token'] = refreshToken
            pollingTokenDict['client_secret'] = clientSecret
            pollingTokenDict['client_id'] = clientId
            pollingTokenDict['username'] = qubeAccountUsername
            pollingTokenDict['product_id'] = productId
            pollingTokenDict['password'] = qubeAccountPassword

        self.writeTokenToJson(tokenDict = pollingTokenDict, tokenJsonFile = tokenJsonFile)

        token = '{} {}'.format('Bearer', pollingTokenDict['access_token'])
        LOGGER.debug("Access Token returned: '{0}'".format(token))
        return token

    def getAuthCodeToken(self, qubeAccountUsername, qubeAccountPassword, email, password, clientId, clientSecret,
                         productId, redirectUri, responseType = 'code', accessType = 'offline',
                         refreshExpiredToken = True, refreshFailedToken = True, tokenJsonFile = None):
        """
        :param qubeAccountUsername:
        :param qubeAccountPassword:
        :param clientId:
        :param clientSecret:
        :param productId:
        :param redirectUri:
        :param qubeAccountUrl:
        :param responseType:
        :param accessType:
        :param refreshExpiredToken:
        :return:
        """

        self.login = login.Login(browser = self.browser, results = self.results)

        if tokenJsonFile is not None and os.path.isfile(tokenJsonFile):
            with open(tokenJsonFile) as tokenFile:
                tokenJson = json.load(tokenFile)

            userInfoList = list(filter(lambda userInfo: userInfo['username'] == qubeAccountUsername and
                                                        userInfo['client_id'] == clientId, tokenJson))
            if userInfoList and refreshFailedToken:
                if refreshExpiredToken:
                    try:
                        return self.refreshToken(token = userInfoList[0]['access_token'], tokenJsonFile = tokenJsonFile)
                    except:
                        pass
                else:
                    return '{} {}'.format(userInfoList[0]['token_type'], userInfoList[0]['access_token'])

        self.login.login(qubeAccountUsername = qubeAccountUsername, qubeAccountPassword = qubeAccountPassword,
                         email = email, password = password, productId = productId, clientId = clientId,
                         redirectUri = redirectUri, responseType = responseType, accessType = accessType)