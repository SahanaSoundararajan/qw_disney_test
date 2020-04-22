import imaplib
import email
import email.header
from datetime import datetime
import logging
from autologging import logged, traced

LOGGER = logging.getLogger(__name__)

@traced
@logged
class EmailUtils():

    def parseDomain(self, username):
        """
        :param username: (str) username
        :return: (json)
        """

        domain = username.split("@")[1].strip().split(".")[0]

        domainDict = {"gmail": ("imap.gmail.com", 993), "yahoo": ("imap.mail.yahoo.com", 993),
                      "qubecinema": ("outlook.office365.com", 993)}

        return domainDict[domain.lower()]

@traced
@logged
class EmailClient():

    def __init__(self, username, password):

        emailUtilsObj = EmailUtils()
        self.smtpServer, self.smtpPort = emailUtilsObj.parseDomain(username = username)
        self.username = username
        self.password = password

        self.login()

    def login(self):
        """
        Create a IMAP client and login to the mailbox
        :param username:
        :param password:
        :return:
        """

        self.client = imaplib.IMAP4_SSL(host = self.smtpServer, port = self.smtpPort)
        self.client.login(self.username, self.password)

    def logout(self):
        """
        Logout from the mailbox
        :return:
        """

        self.client.logout()

    def selectFolder(self, folderName = None):
        """
        Select the folder from the mailbox where we want to read mails
        :param folderName:
        :return:
        """

        if not folderName:
            folderName = "Inbox"
        self.client.select(mailbox = folderName)

    def fetchMails(self, emailFilter = None):
        """
        Fetch mails from the selected folder with search criteria
        :param username:
        :param password:
        :param emailFilter: (dict) example:
                             emailFilter = {
                                              "folder": "OTP",
                                              "from": "noreply@qubecinema.com",
                                              "since": 25-Mar-2019,
                                              "till": 04-Jun-2019,
                                              "visibility": "UNSEEN"
                                          }
        :return: email messages sorted by received dateTime
        """

        searchQuery = "("

        if "visibility" in emailFilter:
            searchQuery = searchQuery + str(emailFilter["visibility"]) + " "
        if "from" in emailFilter:
            searchQuery = searchQuery + 'FROM "{}"'.format(emailFilter["from"]) + " "
        if "subject" in emailFilter:
            searchQuery = searchQuery + 'SUBJECT "{}"'.format(emailFilter["subject"]) + " "
        if "since" in emailFilter:
            searchQuery = searchQuery + 'SINCE "{}"'.format(emailFilter["since"]) + " "
        if "till" in emailFilter:
            searchQuery = searchQuery + 'BEFORE "{}"'.format(emailFilter["till"]) + " "

        searchQuery = searchQuery.rstrip() + ")"
        LOGGER.debug("Search Criteria: {0}".format(searchQuery))

        retCode, messages = self.client.search(None, "{0}".format(searchQuery))

        if retCode != "OK":
            LOGGER.debug("No messages found!")
            return

        if len(messages[0].split()) < 1:
            LOGGER.debug("No emails found for given search criteria")
            return

        messageList = []
        for msgId in messages[0].split():
            msg, messageData = self.client.fetch(msgId, "(BODY.PEEK[])")
            if msg != "OK":
                LOGGER.error("ERROR getting message: {0}".format(msgId))
                return

            emailMessage = {}
            message = email.message_from_string(messageData[0][1].decode("utf-8"))
            emailMessage["message"] = message
            emailMessage["date"] = message["Date"]
            emailMessage["seq"] = msgId.decode('utf-8')
            messageList.append(emailMessage)

        sortedMails = sorted(messageList,
                             key = lambda x: datetime.strptime(x["date"], "%a, %d %b %Y %H:%M:%S %z"),
                             reverse = True)
        return sortedMails

    def readLastUnseenMail(self, emailFilter = None):
        """
        Read the text part of the last Unseen email that matches the search criteria
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
        :return: text part of the email body
        """

        mailList = self.fetchMails(emailFilter = emailFilter)
        if not mailList:
            return

        latestMessage = mailList[0]["message"]
        self.markAsRead(uid = mailList[0]["seq"])

        for part in latestMessage.walk():
            contentType = part.get_content_type()
            disp = str(part.get("Content-Disposition"))
            if contentType == "text/plain" and "attachment" not in disp:
                charset = part.get_content_charset()
                body = part.get_payload(decode = True).decode(encoding = charset, errors = "ignore")
                return body

    def readTextPartFromMail(self, email):
        """
        Read text part from mail which is of multipart type
        :param email: imap email object
        :return: text part fetched from the mail
        """

        for part in email.walk():
            contentType = part.get_content_type()
            disp = str(part.get("Content-Disposition"))
            if contentType == "text/plain" and "attachment" not in disp:
                charset = part.get_content_charset()
                textBody = part.get_payload(decode = True).decode(encoding = charset, errors = "ignore")
                return textBody

    def readHtmlPartFromMail(self, email):
        """
        Read text part from mail which is of multipart type
        :param email: imap email object
        :return: html content fetched from the mail
        """

        for part in email.walk():
            contentType = part.get_content_type()
            disp = str(part.get("Content-Disposition"))
            if contentType == "text/html" and "attachment" not in disp:
                charset = part.get_content_charset()
                htmlBody = part.get_payload(decode = True).decode(encoding = charset, errors = "ignore")
                return htmlBody

    def markAsRead(self, uid):
        """
        Mark a mail as read after reading
        :param username:
        :param password:
        :param uid: unique id of the message
        :return:
        """

        self.client.store(uid, "+FLAGS", "\SEEN")

    def markAsUnread(self, uid):
        """
        Mark a mail as unread if we silently want to read a mail
        :param username:
        :param password:
        :param uid: unique id of the message
        :return:
        """

        self.client.store(uid, "-FLAGS", "\SEEN")