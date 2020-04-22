import sys
import os
import uuid
import logging
import traceback
from autologging import traced, logged
from datetime import datetime, timedelta
import time
import qubeaccount.db
import config
from ui.browser import *
import mail.imap_client


TWO_FACTOR_AUTH_SMS_CODE = 911440
TWO_FACTOR_MAIL_SUBJECT = "One Time Password for your Qube Cinema Account"

LOGGER = logging.getLogger(__name__)

@traced
@logged
class Login(Browser):

    def __init__(self, browser = "chrome", results = None):

        # change it to super().__init__() once existing code migrated to python3
        Browser.__init__(self)
        self.results = results
        if self.results is None:
            self.results = {"resultAttachments": {}, "output": "", "executedWithWarnings": False}

        self.config = config.Config(service = "qubeaccount")
        self.qubeAccountUrl = self.config.url
        self.qubeAccountSenderEmail = self.config.qubeAccountSenderEmail
        self.browser = browser

    def login(self, qubeAccountUsername, qubeAccountPassword, email, password, clientId = None, redirectUri = None,
              responseType = None, productId = None, code = None, accessType = None, isTrustedClient = True,
              allow = True, retryDriverFailures = 5):

        loginUrl = self.qubeAccountUrl + "/dialog/authorize?"

        if code != None:
            loginUrl += "code={0}&".format(code)

        if clientId != None:
            loginUrl += "client_id={0}&".format(clientId)

        if redirectUri != None:
            loginUrl += "redirect_uri={0}&".format(redirectUri)

        if responseType != None:
            loginUrl += "response_type={0}&".format(responseType)

        if productId != None:
            loginUrl += "product_id={0}&".format(productId)

        if accessType != None:
            loginUrl += "access_type={0}&".format(accessType)

        loginUrl = loginUrl.strip("&")

        retryDriverFailureCount = 0
        while True:
            self.launch()
            try:
                self.signIn(loginUrl = loginUrl, qubeAccountUsername = qubeAccountUsername,
                            qubeAccountPassword = qubeAccountPassword, email = email, password = password)
                break
            except Exception as e:
                retryDriverFailureCount += 1
                if retryDriverFailureCount >= retryDriverFailures:
                    raise Exception(e)

        if not isTrustedClient:
            if allow:
                try:
                    WebDriverWait(self.webDriver, 10).until(EC.presence_of_element_located((By.ID, "allow")))
                finally:
                    self.webDriver.save_screenshot("allow.png")
                    self.results["resultAttachments"].update({"allow.png": os.path.realpath("allow.png")})

                self.webDriver.find_element_by_id("allow").click()
                self.webDriver.save_screenshot("allow_clicked.png")
                self.results["resultAttachments"].update({"allow_clicked.png": os.path.realpath("allow_clicked.png")})

            else:
                self.webDriver.find_element_by_id("deny").click()

        self.close()

    def signIn(self, loginUrl, qubeAccountUsername, qubeAccountPassword, email, password):
        """
        signIn: Opens the given Url and enters user name & password and submits it.
        Parameters:
                (driver) webDriver: Selenium driver object to open url
                (str) loginUrl: login url
                (str) username: user name
                (str) password: password
        Return: None
        """

        try:
            self.webDriver.get(loginUrl)
            self.webDriver.find_element_by_id("username").send_keys(qubeAccountUsername)
            self.webDriver.find_element_by_id("password").send_keys(qubeAccountPassword)
            # Finding element by class name
            # webDriver.find_element_by_class_name("loginBtn").click()
            signInBtnXPath = "/html/body/div[1]/div/div/div/div/form/div[4]/button"
            self.webDriver.find_element_by_xpath(signInBtnXPath).click()
            LOGGER.debug("SignIn button is clicked..")
            challengeId = self.webDriver.find_element_by_id("id").get_attribute("value")

            try:
                challengeId = uuid.UUID(challengeId, version = 4)
            except:
                LOGGER.debug("Invalid UUID found for the field id: {challengeId}".format(challengeId = challengeId))

            if email and password is not None:
                time.sleep(10) # Wait to get the mail from qube account else it will read exiting mail
                twoFactorAuthCode = self.readOtp(username = email, password = password)
            else:
                dataBase = db.Db()
                dataBase.updateOtpHash(challengeId = challengeId)
                twoFactorAuthCode = TWO_FACTOR_AUTH_SMS_CODE

            LOGGER.debug("OTP - Two Factor Auth Code: {}\n".format(twoFactorAuthCode))
            self.webDriver.find_element_by_id("verificationCode").send_keys(twoFactorAuthCode,
                                                                            Keys.TAB, Keys.SPACE)
            verifyBtnXPath = "/html/body/div[1]/div[2]/div/div/div/form/div/div[3]/input"
            self.webDriver.find_element_by_xpath(verifyBtnXPath).click()
            LOGGER.debug("Verify button is clicked..")
        except:
            self.webDriver.save_screenshot("signin.png")
            self.results["resultAttachments"].update({"signin_error.png": os.path.realpath("signin.png")})
            self.close()
            raise

    def readOtp(self, username, password, timeout = 60):
        """
        Fetch mails with given search criteria and read OTP from the latest mail
        :param username:
        :param password:
        :param emailFilter: (dict) example:
                             emailFilter = {
                                              "folder": "OTP", # default is 'Inbox'
                                              "from": "noreply@qubecinema.com",
                                              "since": 25-Mar-2019,
                                              "till": 04-Jun-2019,
                                              "visibility": "UNSEEN"
                                          }
        :return: OTP fetched from the mail
        """

        startDate = datetime.now()
        endDate = datetime.now() + timedelta(days = 1)

        self.emailFilter = {
            "folder":     "Inbox",
            "from":       self.qubeAccountSenderEmail,
            "since":      startDate.strftime("%d-%b-%Y"),
            "till":       endDate.strftime("%d-%b-%Y"),
            "visibility": "UNSEEN",
            "subject":    TWO_FACTOR_MAIL_SUBJECT
            }

        self.emailClientObj = imap_client.EmailClient(username = username, password = password)

        startTime = time.time()
        while True:
            if self.emailFilter.get("folder"):
                self.folderName = self.emailFilter["folder"]
                self.emailClientObj.selectFolder(folderName = self.folderName)
            else:
                self.emailClientObj.selectFolder()

            messageBody = self.emailClientObj.readLastUnseenMail(emailFilter = self.emailFilter)

            if not messageBody and time.time() > startTime + timeout:
                self.emailClientObj.logout()
                raise Exception("OTP not received within 30 seconds")
            else:
                otp = messageBody.split("One Time Password is *")[1].strip().split("*.")[0]
                self.emailClientObj.logout()
                return otp

            time.sleep(5)