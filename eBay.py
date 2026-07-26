from ebaysdk.finding import Connection as finding
from bs4 import BeautifulSoup

Keywords = input("What are you searching for? (E.g.: White Piano)\n")
api = finding(appid="KarimShr-Producti-PRD-60e716915-1a6c9db1", config_file=None, siteid="15", debug=True)
api_request = {"keywords" : Keywords, "outputSelector" : "SellerInfo"}

response = api.execute("findItemsByKeywords", api_request)
soup = BeautifulSoup(response.content, "lxml")

totalentries = int(soup.find("totalentries").text)
items = soup.find_all("item")

input(items[0])

# for item in items:
#     cat = item.categoryname.string.lower()
#     title = item.title.string.lower()
#     price = int(round(float(item.currentprice.string)))
#     url = item.viewitemurl.string.lower()

#     print('________')
#     print('cat:\n' + cat + '\n')
#     print('title:\n' + title + '\n')
#     print('price:\n' + str(price) + '\n')
#     print('url:\n' + url + '\n')
#     input()