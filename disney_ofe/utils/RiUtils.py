import os
import sys
import logging
import dateutil.parser
import calendar
import simplejson
import uuid
import random
import json
import time
from datetime import datetime

import pytz
import urllib
import contextlib
import socket

import smtplib
import sys

if sys.version_info[0] < 3:
    from email.MIMEMultipart import MIMEMultipart
    from email.MIMEBase import MIMEBase
    from email.MIMEText import MIMEText
    from email.Utils import COMMASPACE, formatdate
    from email import Encoders

else:
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email.mime.text import MIMEText
    from email.utils import COMMASPACE, formatdate
    from email import encoders as Encoders

LOGGER = logging.getLogger()
LOGGER.addHandler(logging.NullHandler())

class JsonParser:

    def __init__(self, jsonData):
        """Loads the given json file
        """

        LOGGER.debug('Inside JsonParser init...')
        jsonData = str(jsonData)
        if os.path.isfile(jsonData):
            jsonData = open(jsonData).read()
        self.data = simplejson.loads(jsonData)

    def getAllKeys (self):
        LOGGER.debug('Inside getAllKeys...')
        return self.data.keys()

    def getKeyValueItem(self, key, keyName = None,\
            keyValue = None):
        """Returns the value for the given key, keyName & keyValue
        Ex: "CPLs" : [{"Name" : "Test", "ID" : "Guid", "Path" : "uri"},
            {"Name" : "Test1", "ID" : "Guid1", "Path" : "uri1"}]
        For the given key -> CPLs, keyName -> 'Name' & keyValue -> 'Test'
        CPL dictionary with 'Name' -> 'Test' will be returned.
        If the keyName & keyValue is None entire CPLs list will be returned.
        """

        LOGGER.debug('Inside getKeyValueItem...')
        if key:
            keys = self.data[key]
            if keyName and keyValue:
                for key in keys:
                    if key[keyName] == keyValue:
                        return key
            else:
                return keys
        LOGGER.debug('Returning None.')
        return None

    def getDictByKeyValueFromList(self, key, value):

        LOGGER.debug('Inside getDictByKeyValueFromList...')
        for item in self.data:
            if key in item:
                if item[key] == value:
                    return item
        LOGGER.debug('value not found. Returning false.')
        return False

def GetValueListOfKey(listOfDict, key):
    """
    Returns a value list of a particular key in a list of dictionary
    Parameters:
        list(dict) : listOfDict
        str : key, key name of the dictionary
    Return:
        list(str) : list of values of the given key in the list of dict
    """

    LOGGER.debug('Inside GetValueListOfKey...')
    valueList = []
    for item in listOfDict:
        valueList.append(item[key])
    return valueList

def VerifyGuid(guid = None):
    """Checks and return UUID as string if it is valid,
       otherwise throws exception.
    """

    LOGGER.debug('Inside VerifyGuid...')
    try:
        return str(uuid.UUID(guid))
    except Exception:
        LOGGER.error("Input guid {0} is invalid.".format(guid))
        raise Exception("Input guid {0} is invalid.".format(guid))

def VerifyBoolean(boolean = None):
    """Returns bool value for given input.
    """

    LOGGER.debug('Inside VerifyBoolean...')
    booleanTrueList = ['true', '1', 't', 'y', 'yes']
    booleanFalseList = ['false', '0', 'f', 'n', 'no']

    if (str(boolean).replace(' ', '').lower() in booleanTrueList):
        return True
    elif (str(boolean).replace(' ', '').lower() in booleanFalseList):
        return False
    else:
        LOGGER.error("Input boolean is invalid.")
        raise Exception("Input boolean is invalid.")

def NewGuid():
    """Returns a random UUID
    """

    LOGGER.debug('Inside NewGuid...')
    return str(uuid.uuid4())

def RandomNumber(numberOfDigits = 3, strictToDigits = False):
    """Returns a random number. If the numberOfDigits is three then
    a three digit number will be returned in the range 0 to 999 when strict is False.
    When strict is true, a three digit numbe will be returned in the range 100 to 999
    Parameter:
        (int) numberOfDigits
    Return:
        (int) random number which will have length between 1 to number of digits
    """

    LOGGER.debug('Inside RandomNumber...')

    start = 0
    if strictToDigits:
        start = 10 ** (numberOfDigits - 1)

    val = random.randint(start, (10 ** numberOfDigits) - 1)
    LOGGER.debug('Generated random int {val}'.format(val = val))
    return val

def GetTimeZoneOffset(dateTimeStr, timeZone):
    """
    GetTimeZoneOffset - Will return the time zone offset in the format +HH:MM or -HH:MM
    Params:
        dateTimeStr: DateTime as str. If it in DateTime obj it will be converted to str.
        timeZone: timeZone as str. Ex: US/Pacific
    Return:
        timeZoneOffset: timeZoneOffset as str. Will be in the format +HH:MM or -HH:MM
    """

    timeZone = pytz.timezone(timeZone)
    timeZoneOffset = timeZone.localize(dateutil.parser.parse(str(dateTimeStr))).strftime('%z')
    timeZoneOffset = "{0}:{1}".format(timeZoneOffset[:3], timeZoneOffset[-2:])
    return timeZoneOffset

def GetCurrentDateTime():
    """Returns the current date time in YYYY-MM-DD_HH-MM-SS format
    Return : current date time in string format
    """

    LOGGER.debug('Inside GetCurrentDateTime...')
    currentDateTime = str(datetime.now()).replace(':', '-').\
        replace(' ', '_')[:19]
    LOGGER.debug('Datetime: {date_time}'.format(date_time = currentDateTime))
    return currentDateTime

def GetHostIpByName(hostName = None):
    """Returns the ip for given host.
    If hostName is None local machine ip will be returned.
    Parameter:
        Optional:
            (str) hostName
    Return:
        (str) IpAddress
    """

    LOGGER.debug('Inside GetHostIpByName...')
    if not hostName:
        hostName = socket.gethostname()
    ip = socket.gethostbyname(hostName)
    LOGGER.debug('HostIp: {ip}'.format(ip = ip))
    return ip

def ReadFileFromFtp(ftpFilePath, fileName):
    """Returns requested file as string.
    Parameter : ftp file path, filename
    Return : string.
    """

    LOGGER.debug('Inside ReadFileFromFtp...')
    with contextlib.closing(urllib.urlopen(ftpFilePath + '//' +\
            fileName)) as urlFile:
        return urlFile.read()

def DeleteFiles(files = []):
    """
    Deletes the given list of files if exists.
    """

    LOGGER.debug('Inside DeleteFiles...')
    for file in files:
        DeleteFile(file)
    LOGGER.debug('Successfully deleted all files.')

def DeleteFile(file):
    """
    Deletes the given file if exists.
    """

    LOGGER.debug('Inside DeleteFile...')
    try:
        if os.path.isfile(file):
            os.remove(file)
    except Exception as e:
        LOGGER.error("File deletion failed. Error: {err}".format(err = e))
    LOGGER.debug('Successfully deleted file: {file}'.format(file = file))

def StringToList(inputString):
    """Converts inputString to list of string and returns. If the
    inputString is list then same will be return. Otherwise
    exception will be raised.
    Parameter: (str) string
    """

    LOGGER.debug('Inside StringToList...')
    convertToStringTypes = [int, float]

    if sys.version_info[0] < 3:
        convertToStringTypes += [long, unicode]

    if type(inputString) in convertToStringTypes:
        inputString = str(inputString)

    if isinstance(inputString, str):
        return [inputString]
    elif isinstance(inputString, list):
        return inputString
    elif inputString == None:
        LOGGER.debug('Input string is None. Returning empty list.')
        return []

    msg = "inputString is not a valid 'str' or 'list'. Actual type is {0}".format(type(inputString))
    LOGGER.error(msg)
    raise TypeError(msg)

def XmlDurationToTime(duration):
    """
    Converts XML duration to time.struct_time object. Input should be in any of the following formats,
        PTnHnMn.nS or PTnHnMnS or PTnHnM or PTnHn.nS
        PTnMn.nS or PTnMnS or PTnM
        PTn.nS or PTnS
    where 'n' is int
    Parameter: duration
    Return: time.struct_time
    """

    LOGGER.debug('Inside XmlDurationToTime...')
    format = "PT"
    if 'H' in duration:
        format += "%HH"
    if 'M' in duration:
        format += "%MM"
    if 'S' in duration:
        if '.' in duration:
            format += "%S.%fS"
        else:
            format += "%SS"

    res = time.strptime(duration, format)
    LOGGER.debug('time: {res}'.format(res = res))
    return res

def DateTimeToEpoch(dateTime):

    LOGGER.debug('Inside DateTimeToEpoch...')
    return calendar.timegm(dateutil.parser.parse(dateTime).utctimetuple())

def EpochToDateTime(epochTime, timeZone = '+05:30'):
    """Converts the given epoch time to date time with corresponding to
    given timeZone value.
    Parameters:
        Must: (long) epochTime in seconds
        Optional: (str) timeZone should be in the format '+HH:MM' or
                  '-HH:MM'
    Return:
        Returns date time in the format YYYY-MM-DDTHH:MM:SS+timeZone
    """

    LOGGER.debug('Inside EpochToDateTime...')
    hoursAndMins = timeZone.split(':')
    hoursToAdd = int(hoursAndMins[0])
    minsToAdd = int(hoursAndMins[1])


    if hoursToAdd >= 0:
        secondsToAdd = (hoursToAdd * 60 * 60) + (minsToAdd * 60)
    else:
        """If timeZone is negative then we are negating minsToAdd with
        hoursToAdd. So we will get the seconds in negative."""
        secondsToAdd = (hoursToAdd * 60 * 60) - (minsToAdd * 60)

    epochTime = epochTime + secondsToAdd
    res = time.strftime("%Y-%m-%dT%H:%M:%S{0}".format(timeZone), time.gmtime(epochTime))
    LOGGER.debug('DateTime: {res}'.format(res = res))
    return res

def SendMail(send_from, send_to, subject, text):

    LOGGER.debug('Inside SendMail...')
    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime = True)
    msg['Subject'] = subject

    # msg.attach( MIMEText(text) )

    smtp = smtplib.SMTP('titan.realimage.co.in')
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.close()
    LOGGER.debug('Mail sent successfully.')

def WriteToFile(fileName, fileContent, folderPath = None):
    """
    Checks if the given folderPath exists if not creates the folder and creates a file with given name
    and writes the given filecontent into the file.
        (str) folderPath : complete folder path
        (str) filename: filename to be created
        (str) filecontent: content to be written to file
    """

    LOGGER.debug('Inside WriteToFile...')
    if not folderPath:
        filePath = fileName
    else:
        if not os.path.exists(folderPath):
            os.makedirs(folderPath)
        filePath = os.path.join(folderPath, fileName)

    with open(filePath, 'w', 0) as f:
        if (isinstance(fileContent, list) or isinstance(fileContent, dict)):
            json.dump(fileContent, f)
        else:
            f.write(fileContent)
    LOGGER.debug('Written to file: {filePath} successfully.'.format(filePath = filePath))

def IterateFilesFromFolder(folderPath, recursive = False, relativePath = False):
    """Returns file names from given folder path. If recursive is True then entire file list will be return.
    Prams:
        (str) folderPath : folderPath to get files.
        (bool) recursive : True to recursively seek for files else False
    Return:
        (list) list of files in folderPath.
    """
    LOGGER.debug('Inside IterateFilesFromFolder...')
    fileList = []

    if recursive:
        for folder in IteratorFolders(folderPath):
            for file in IterateFilesFromFolder(folderPath = folder, relativePath = relativePath):
                if relativePath:
                    fileList.append(os.path.relpath(os.path.join(folderPath, file), start = folderPath))
                else:
                    fileList.append(file)
    else:
        for file in os.listdir(folderPath):
            if os.path.isfile(os.path.join(folderPath, file)):
                if relativePath:
                    fileList.append(os.path.relpath(os.path.join(folderPath, file), start = folderPath))
                else:
                    fileList.append(os.path.join(folderPath, file))

    return fileList

def IteratorFolders(folderPath):
    """Returns folder name from given folder path
    """

    for folders in os.walk(folderPath):
        yield folders[0]

def Unique_list_of_dict(listOfDict):
    """
    Returns unique list of dict from the given list of dict
    Param:
        list(dict) : listOfDict
    return:
        list(dict) : listOfDict
    """

    uniqueListOfDict = []

    for item in listOfDict:
        if item not in uniqueListOfDict:
            uniqueListOfDict.append(item)

    return uniqueListOfDict

def Ordered(obj):
    """
    Ordered: sorts list or dict object
    params:
        obj: can be a list or dict or json
    Returns:
        sorted obj. Output will be,
            list of tuple in case of dict
            list in case of list
            Nested list of tuple for complex json
    """

    if isinstance(obj, dict):
        return dict(sorted((k, Ordered(v)) for k, v in obj.items()))
    if isinstance(obj, list):
        return list(sorted(Ordered(x) for x in obj))
    else:
        return obj