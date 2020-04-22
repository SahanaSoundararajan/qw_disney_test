import platform
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../utils/Modules')))
from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui  import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
import platform
import psutil
import logging
import traceback
from autologging import traced, logged

CHROME_OPTIONS = webdriver.ChromeOptions()
CHROME_OPTIONS.add_argument("--no-sandbox")
CHROME_OPTIONS.add_argument("--disable-setuid-sandbox")

LOGGER = logging.getLogger(__name__)

@traced
@logged
class Browser():

    def __init__(self, browser = "chrome"):

        self.browser = browser
        self.display = None
        self.webDriver = None

    def launch(self, chromeOptions = CHROME_OPTIONS):
        """
        launchBrowser
        :param chromeOptions: webdriver chrome options
        :return: webdriver, display
        """

        operatingSystem = platform.system()

        if self.browser == 'chrome':
            try:
                if operatingSystem.lower() == "windows":
                    self.webDriver = webdriver.Chrome(chrome_options = chromeOptions)
                else:
                    self.webDriver = webdriver.Chrome(chrome_options = chromeOptions)
            except:
                from pyvirtualdisplay import Display
                self.display = Display(visible = 0, size = (1920, 1080))
                self.display.start()
                chromeOptions.add_argument("--headless")
                # Assuming headless will configured only Chrome
                self.webDriver = webdriver.Chrome(chrome_options = chromeOptions)
        elif self.browser.lower() == 'ie':
            if operatingSystem.lower() == "windows":
                self.webDriver = webdriver.Ie('Utils/Modules/selenium/webdriver/ie/IEDriverServer.exe')
            else:
                self.webDriver = webdriver.Ie()
        elif self.browser.lower() == 'firefox':
            self.webDriver = webdriver.Firefox()
        elif self.browser.lower() == 'phantomjs':
            self.webDriver = webdriver.PhantomJS()
        else:
            raise Exception("Specified browser doesn't not exists")

    def close(self):
        """
        close - close browser
        :return: None
        """

        if self.display:
            processId = 0
            try:
                processId = self.display.pid
                self.display.stop()
            except:
                LOGGER.error("Error while stopping display. {0}".format(traceback.format_exc()))
                try:
                    p = psutil.Process(processId)
                    p.terminate()
                except:
                    LOGGER.error("Error while terminating display process. {0}".format(traceback.format_exc()))

        processId = 0
        try:
            processId = self.webDriver.service.process.pid
            self.webDriver.close()
            self.webDriver.quit()
        except:
            LOGGER.error("Error while closing webDriver. {0}".format(traceback.format_exc()))
            try:
                p = psutil.Process(processId)
                p.terminate()
            except:
                LOGGER.error("Error while terminating webDriver process. {0}".format(traceback.format_exc()))

    def highlight(self, element):
        """
        highlight - highlight the given element to take snapshot
        :param element: browser element to highlight
        :return: None
        """

        """Highlights (blinks) a Selenium Webdriver element"""
        webDriver = element._parent

        def applyStyle(s):
            webDriver.execute_script("arguments[0].setAttribute('style', arguments[1]);", element, s)

        originalStyle = element.get_attribute('style')
        originalStyle("background: yellow; border: 2px solid red;")
        time.sleep(30)
        applyStyle(originalStyle)

