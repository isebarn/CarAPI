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

ad_base_url = "https://bland.is/classified/entry.aspx?classifiedId={}"
list_url = "https://bland.is/solutorg/farartaeki/nyir-notadir-bilar-til-solu/?categoryId=17&sub=1&page={}"
props = ["Framleiðandi", "Undirtegund", "Tegund", "Ár", "Akstur", "Eldsneyti", "Skipting", "Hjóladrifin", "Skipti", "Fjöldi sæta", "Fjöldi dyra", "Fjöldi strokka", "Skoðaður", "Litur"]
months = ["", "janúar", "febrúar", "mars", "apríl", "maí", "júní", "júlí", "ágúst", "september", "október", "nóvember", "desember"]


page_list_class = "box classifiedentry pagenr{}"
ad_url_key = "data-url"

def fetchPage(page):
  http = urllib3.PoolManager()
  r = http.request("GET", page)
  return r.data


def getAllAdsFromPageThread(page_number, queue):
  result = getAllAdsFromPage(page_number)
  queue.put(result)

def getAllAdsFromPage(page_number):
  page = fetchPage(list_url.format(page_number))
  soup = BeautifulSoup(page, features="lxml")
  car_list = soup.find_all("div", class_= page_list_class.format(page_number))

  return [x[ad_url_key] for x in car_list]

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


  result = re.search(r'\d+', result)

  if result == None:
    return 0

  result = result.group()
  result = int(result)

  if result > 2**31:
    result = 0

  return result

def getDescription(soup):
  result = soup.find("p", itemprop="description").text
  return result

def tryGetCar(url, queue = None):
  try:
    return getCar(url, queue)

  except Exception as e:
    print(url)
    error = {}
    error["Text"] = str(e)
    error["Time"] = datetime.now()
    error["URL"] = url

    Operations.LogError(error)

def getCar(url, queue = None):
  url = ad_base_url.format(str(url))

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

def check(car_id):
  page = fetchPage(ad_base_url.format(str(car_id)))
  soup = BeautifulSoup(page, features="lxml")

  if (soup.find("span", class_="product_headline")) == None:
    Operations.MarkCarSold(car_id)

    return True

  return False

class Parser:

  def Update():
    ads = []
    threads = []
    queue = Queue()

    # Start threads where each thread reads a single list page
    for idx in range(0,40):
      x = threading.Thread(target=getAllAdsFromPageThread, args=(idx, queue))
      x.start()
      threads.append(x)

    # Wait for threads to finish
    for thread in threads:
      thread.join()
      page_data = queue.get()
      ads.append(page_data)

    # parse the ID's from the ad urls and get a unique list
    live_ads = [int(getClassifiedId(item)) for sublist in ads for item in sublist]
    live_ads = set(live_ads)

    # Fetch all from db that have not been mark sold
    unsold_saved_ads = Operations.GetAllIds()

    # save new
    unsaved_ads = [x for x in live_ads if x not in unsold_saved_ads]
    split = 10
    unsaved_ads_chunks = [unsaved_ads[x:x+split] for x in range(0, len(unsaved_ads), split)]
    queue = Queue()
    cars = []

    for i, url_sect in enumerate(unsaved_ads_chunks):
      threads = []
      print("Thread section {}/{}".format(i,len(unsaved_ads_chunks)), file=sys.stdout)

      for url in url_sect:
        x = threading.Thread(target=tryGetCar, args=(url, queue))
        x.start()
        threads.append(x)

      for thread in threads:
        thread.join()
        car = queue.get()
        cars.append(Car(car))

    Operations.SaveCars(cars)

    # mark sold
    unsold_saved_ads = Operations.GetUnsoldIDs()
    saved_ads_ids_minus_live = [x for x in unsold_saved_ads if x not in live_ads]

    sold = []
    for ad in saved_ads_ids_minus_live:
      if check(ad):
        sold.append(ad)

    result = { "new": unsaved_ads, "sold": sold }

    Operations.LogUpdate(result)

    return result

if __name__ == "__main__":
  Parser.Update()
