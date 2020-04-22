import view
import unittest
import logging
import csv
import os
from autologging import logged, traced
import start_mock
from distributors_admin import oauth as distributorAdminOAuth

TOKEN_JSON_ADMIN = os.path.abspath('../DistributorsAdminTokens.json')



@traced
@logged
class TestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        self.results = {"resultAttachments": {}, "output": "", "executedWithWarnings": False}
        super(TestCase, self).__init__(*args, **kwargs)
        self.logging = logging.getLogger(__name__)
        self.setUpDone = False

    def setUp(self):

        if not self.setUpDone:

            self.mock = start_mock.StartMock(results = self.results)

            self.timezone = "Asia/Kolkata"

            distributorAdminTokenObj = distributorAdminOAuth.OAuth(userAccount = "distributorsAdmin",
                                                                   results = self.results, useMock = False,
                                                                   tokenJsonFile = TOKEN_JSON_ADMIN,
                                                                   oauthType = "Polling")

            self.distributorsAdminToken = distributorAdminTokenObj.token
            
    


    def test_place_new_order(self): #Disney places a new order booking
        result = view.new_order_booking()
        self.assertEquals(result, 200)
    
    def test_new_order_download(self): #Download the new_orders.csv 
        result = view.order_download('New')
        self.assertTrue(result, True)

    def test_order_upload(self): #Modify QW Status in the new_order.csv and reupload to disney
        new_status = 'Accepted'
        result = view.disney_status_upload(new_status)
        self.assertEquals(result, 200)

    def test_inflight_order_download(self): #Download the inflight order
        result = view.order_download('Inflight')
        self.assertTrue(result, True)



if __name__ == '__main__':
    unittest.main()
        
