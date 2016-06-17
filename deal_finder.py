#!/usr/bin/python3
import time
import sys
import logging
from datetime import datetime

import pymysql.cursors

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import StaleElementReferenceException

from urllib.parse import urlparse
from operator import itemgetter

from groupon_scraper import groupon_scraper
from livingsocial_scraper import livingsocial_scraper

"""
This script will scrape off the first page of yipit in each city from list in cities.txt
It will then figure if the deal exists in database:
	if it exists, then it will ignore.
	if it is a new dea, then add to database.
"""

def crawl(city, db_links):
    city_url = "http://yipit.com/search/?q=&loc=" + city + "&sort=recency&page=" #i.e. Toronto
    page = 1
    REAL_LINKS = [] # container for all the hrefs 
    driver = webdriver.Chrome()

    #first call
    try: # Try looking for the javascript injection
        driver.get(city_url+str(page))

        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="pagination-nav"]/ul'))) 
        xpath = '//*[@id="pagination-nav"]/ul[1]'
        max_page = int(driver.find_element_by_xpath(xpath).text.split()[-1])
        print("maximum page is :", max_page)
    except Exception as e:
        print("exception at loading city webpage.")
        logging.basicConfig(level = logging.DEBUG, filename = 'exception.log')
        logging.exception(e)
        pass
    # Below while loop goes up until maxpage acquired from the block above.
    # change them to a single number as desired to limit the navigation maximum page.
    while page < 2: #max_page:
        REAL_LINKS = makeRequest(driver, REAL_LINKS, city_url, page, city, db_links)
        driver = webdriver.Chrome()
        page += 1
    driver.close()
    driver.quit()
    return REAL_LINKS

def makeRequest(driver, REAL_LINKS, url, page, city, db_links):
    print(city,"page:",page)
    url = url + str(page) # i.e. http://yipit.com/search/?q=&loc=Toronto&sort=recency&page=1
    driver.get(url) # yipit toronto as recency
    yipit_links = [] # temporary yipit links storage
    try: # Try looking for the javascript injection
        elements = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="inner-deals"]/div'))) # look for the deals list, by xPath
        for e in driver.find_elements_by_class_name('deal_url'): # find the "deal card"
            link_to_crawl = e.get_attribute("href")
            if (link_to_crawl not in yipit_links): # do not add duplicates
                yipit_links.append(link_to_crawl)        
    except Exception as ex:
        logging.basicConfig(level = logging.DEBUG, filename = 'exception.log')
        logging.exception(ex)
        pass            

    for link in yipit_links: # for each yipit links, check for the actual links
        count = 0
        while True and count < 10:
            try:
                driver.get(link)
            except Exception as e:
                print("Exception while loading retrying", link)
                count += 1
                continue
            else:
                break;
        waittime = 20 #default limit waittime count. 
        waitForLoad(driver, waittime) # wait for redirection
        current_url = driver.current_url #update current url
        html = driver.page_source
        
        if 'groupon' in current_url:
            if not current_url.split("?")[0] in db_links:
                groupon_scraper(html, city, 0) # 0 because this is NOT tracker.
        elif 'livingsocial' in current_url:
            if not current_url.split("?")[0] in db_links:
                livingsocial_scraper(html, city, 0)
            
        
        if (current_url not in REAL_LINKS) and ("yipit.com" not in current_url):
            REAL_LINKS.append(current_url)
            #print(current_url)
        else:
            if current_url in REAL_LINKS:
                print(current_url + " is already in the list.")
                with open("exception_links.txt", "a") as el:
                    el.write("duplicate link:")
                    el.write(current_url + "\n")
            else:
                print("Redirection failed at " + current_url)
                with open("exception_links.txt", "a") as el:
                    el.write("redirection failed at")
                    el.write(current_url + "\n")
    driver.delete_all_cookies()
    driver.close()
    driver.quit()
    return REAL_LINKS


def waitForLoad(driver, limit):
    elem = driver.find_element_by_tag_name("html") 
    count = 0
    manual_switch = True
    while True:
        count += 1
        if count > limit and manual_switch: # timeout limit.
            try:
                element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div/div[3]'))) 
                # look for the manual link
                element.click()
                print("clicked the manual link.")
            except Exception as e:
                print("exception occured while waiting...")
                print(e)
                pass
            count = 0
            manual_switch = False
        elif not manual_switch:
            return
        time.sleep(.5) #wait 0.5 second per count.
        try:
            # check if the page is redirected from earlier html.
            if elem != driver.find_element_by_tag_name("html"):
                return
        except StaleElementReferenceException:
            logging.basicConfig(level = logging.DEBUG, filename = 'exception.log')
            logging.exception(ex)
            return

def getdblink(city):
    connection = pymysql.connect(host='localhost',
                     user='root',
                     password='',
                     db='', 
                     charset='utf8mb4',
                     cursorclass=pymysql.cursors.DictCursor)
    try:
        with connection.cursor() as cursor:
            sql = "SELECT href FROM `deal_detail` WHERE `city` = %s"
            cursor.execute(sql, city)
            hrefs = cursor.fetchall()
    except Exception as e:
        print(e)
        pass
    finally:
        connection.close()

    href_list = []
    for i in hrefs:
        if not i['href'] in href_list:
            href_list.append(i['href'])

    print(href_list)
    return href_list


if __name__ == "__main__":
    with open("cities.txt") as f: # Open file to read yipit city codes.
        cities = f.readlines() # Store each city codes into a list.
    
    #crawl("toronto", getdblink("toronto"))
    #crawl("new-york", getdblink("new-york"))
    
    for city in cities: # For each city in list of cities stored.
        db_links = getdblink(city)
        real_links = crawl(city, db_links)        
    

