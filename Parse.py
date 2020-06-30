from bs4 import BeautifulSoup
import urllib3
import sys
from datetime import datetime, timedelta
import urllib.parse as urlparse
from urllib.parse import parse_qs
from ORM import Car, Operations

base_url = "https://bland.is"
list_url = base_url + "/solutorg/farartaeki/nyir-notadir-bilar-til-solu/?categoryId=17&sub=1&page={}"
props = ["Framleiðandi", "Undirtegund", "Tegund", "Ár", "Akstur", "Eldsneyti", "Skipting", "Hjóladrifin", "Skipti", "Fjöldi sæta", "Fjöldi dyra", "Fjöldi strokka", "Skoðaður", "Litur"]
months = ["", "janúar", "febrúar", "mars", "apríl", "maí", "júní", "júlí", "ágúst", "september", "október", "nóvember", "desember"]


page_list_class = "box classifiedentry pagenr{}"
ad_url_key = "data-url"

def fetchPage(page):
  http = urllib3.PoolManager()
  r = http.request("GET", page)
  return r.data


def getAllAdsFromPage(page_number):
  page = fetchPage(list_url.format(page_number))
  soup = BeautifulSoup(page, features="lxml")
  car_list = soup.find_all("div", class_= page_list_class.format(page_number))

  return [x[ad_url_key] for x in car_list]

def getAllAdsInPageRange(first, last):
  idx = [getAllAdsFromPage(page) for page in range(first, last)]
  return [item for sublist in idx for item in sublist]

def getElement(soup, tag_string, tag_type="td"):
  result = ""

  try:
    element = soup.find(tag_type, string=tag_string)

    if (element != None):
      result =  element.find_next_sibling(tag_type).text

  except:
    print(sys.exc_info())

  return result

def parseDate(date):
  date = date.replace(',', '')
  date = date.replace('.', '')
  date = date.replace(':', ' ')

  split_expiration = date.split(' ')

  if len(split_expiration) != 6:
    return datetime.now()

  weekday = split_expiration[0]
  day = int(split_expiration[1])
  month = int(months.index(split_expiration[2]))
  year = int(split_expiration[3])
  hour = int(split_expiration[4])
  minute = int(split_expiration[5])

  return datetime(year, month, day, hour, minute)

def getUser(soup):
  return soup.find("a", class_="sendPrivateMessage nobbq messageUser")["data-user"]

def getClassifiedId(url):
  parsed = urlparse.urlparse(url)
  return parse_qs(parsed.query)['classifiedId'][0]

def getCar(url):
  url = base_url + url

  page = fetchPage(url)
  soup = BeautifulSoup(page, features="lxml")

  data = {key: getElement(soup, key) for key in props}

  print(url)
  expiration = getElement(soup, "Rennur út", "p")
  date = parseDate(expiration)
  data["Created"] = date - timedelta(days=60)

  data["User"] = getUser(soup)

  data["Id"] = getClassifiedId(url)

  return data

class Parser:

  def parseAll():
    a = getAllAdsInPageRange(0,1)

    newlist = [int(getClassifiedId(x)) for x in a]
    b = Operations.GetAllIds()
    notsaved = [x for x in newlist if x not in b]

    a = [x for x in a if int(getClassifiedId(x)) in notsaved]

    for x in a:
      car = getCar(x)
      Operations.SaveCar(Car(car))

    return len(a)
