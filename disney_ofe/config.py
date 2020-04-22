import json
import os
from autologging import traced, logged
import logging

LOGGER = logging.getLogger(__name__)


@traced
@logged
class Config:

    def __init__(self, service, configFolderPath = None):
        """
        param:
           (str) service: service name. Which will be the json file name as well ex: qubeaccount.json is json file
            then service is qubeaccount
        """

        if not configFolderPath:
            configFolderPath = os.path.abspath(os.path.join(os.path.dirname(__file__), "../configs"))

        with open("{path}/{fileName}.json".format(path = configFolderPath, fileName = service)) as configJson:
            config = json.load(configJson)

        sut = {}
        if os.path.isfile("Sut.json"):
            with open("Sut.json") as sutJson:
                sut = json.load(sutJson)

        # taking only the service section from SUT which will have all other services configs
        sut = sut.get(service, {})

        for key, value in config.items():
            value = sut.get(key, value)
            if isinstance(value, str) and value[:1] == "$":
                sut[key] = os.environ[value[1:]]
            setattr(self, key, sut.get(key, value))

        for key, value in sut.items():
            if key not in config:
                if isinstance(value, str) and value[:1] == "$":
                    sut[key] = os.environ[value[1:]]
                setattr(self, key, sut.get(key))