from bs4 import BeautifulSoup
import urllib3
import time
import sys
from datetime import datetime, timedelta
import urllib.parse as urlparse
from urllib.parse import parse_qs
from ORM import Car, Operations
import threading
from multiprocessing import Queue
import re

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
  user = soup.find("a", class_="sendPrivateMessage nobbq messageUser")
  if user is not None:
    return user["data-user"]
  else:
    return ""

def getClassifiedId(url):
  parsed = urlparse.urlparse(url)
  return parse_qs(parsed.query)['classifiedId'][0]

def getPrice(soup):
  result = soup.find("h5", itemprop="price").text
  result = result.replace('.', '')
  result = result.replace(' ', '')

  if 'Tilboð' in result:
    return 0

  result = re.search(r'\d+', result).group()
  return int(result)

def getDescription(soup):
  result = soup.find("p", itemprop="description").text
  #cleaner = re.compile(r'<.*?>')
  #result = re.sub(cleaner, '', result)
  return result

def getCar(url, queue = None):
  url = base_url + "/classified/entry.aspx?classifiedId=" + str(url)

  page = fetchPage(url)
  soup = BeautifulSoup(page, features="lxml")

  data = {key: getElement(soup, key) for key in props}

  expiration = getElement(soup, "Rennur út", "p")
  date = parseDate(expiration)
  data["Created"] = date - timedelta(days=60)

  data["User"] = getUser(soup)

  data["Id"] = getClassifiedId(url)

  data["Price"] = getPrice(soup)

  data["Description"] = getDescription(soup)

  if queue is not None:
    queue.put(data)
  else:
    return data

def check(queue, url):
  page = fetchPage(url)
  soup = BeautifulSoup(page, features="lxml")

  if (soup.find("span", class_="product_headline")) == None:
    car_id = getClassifiedId(url)
    Operations.MarkCarSold(car_id)

    queue.put(True)

  queue.put(False)


class Parser:


  def checkSold():
    ids = Operations.GetUnsoldIDs()

    base_ad_url = base_url + "/classified/entry.aspx?classifiedId="

    urls = [base_ad_url + str(x) for x in ids]
    split = len(urls)//20
    split_urls = [urls[i::split] for i in range(split)]
    queue = Queue()
    sold = 0

    for i, url_sect in enumerate(split_urls):
      threads = []
      print("Thread section {}/{}".format(i,split))

      for url in url_sect:
        x = threading.Thread(target=check, args=(queue, url))
        x.start()
        threads.append(x)

      for thread in threads:
        thread.join()
        sold += 1 if queue.get() else 0

    return sold



  def parseAll():
    a = getAllAdsInPageRange(0,40)
    a = [int(getClassifiedId(x)) for x in a]
    a = set(a)
    b = Operations.GetAllIds()

    urls = [x for x in a if x not in b]

    split = len(urls)//10
    split_urls = [urls[i::split] for i in range(split)]

    queue = Queue()
    cars = []

    for i, url_sect in enumerate(split_urls):
      threads = []
      print("Thread section {}/{}".format(i,split))

      for url in url_sect:
        x = threading.Thread(target=getCar, args=(url, queue))
        x.start()
        threads.append(x)

      for thread in threads:
        thread.join()
        car = queue.get()
        cars.append(Car(car))

    print("Saving")
    Operations.SaveCars(cars)
    print("Saved")

    return len(cars)


if __name__ == "__main__":
  Parser.parseAll()
  '''
  a = getCar("/classified/entry.aspx?classifiedId=4203603")
  for k,v in a.items():
    print("{}: {}".format(k,v))
  '''
