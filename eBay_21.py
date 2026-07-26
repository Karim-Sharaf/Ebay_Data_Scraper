import os
from ebaysdk.finding import Connection# as finding

from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("api_key")

import datetime

class Ebay_21(object):
    def __init__(self, API_KEY):
        self.api_key = API_KEY

    ## N1:
    def fetch(self):
        # pass
        try:
            api = Connection(appid=self.api_key, config_file=None, siteid="15", debug=True)
            response = api.execute("findItemsAdvanced", {"keywords" : "legos"})
            print(response.reply)

            assert(response.reply.ack == "Success")
            assert(type(response.reply.timestamp) == datetime.datetime)
            assert(type(response.reply.searchResult.item) == list)

            item = response.reply.searchResult.item[0]
            assert(type(item.listingInfo.endTime) == datetime.datetime)
            assert(type(response.dict()) == dict)
        
        except ConnectionError as e:
            print(e)
            print(e.response.dict())

    def parse(self):
        pass

## Main Driver:

if __name__ == "__main__":
    # print(API_KEY)
    E = Ebay_21(API_KEY)
    # E = Ebay_21("KarimShr-Producti-PRD-60e716915-1a6c9db1")
    E.fetch()
    E.parse()