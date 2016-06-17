#!/usr/bin/python3
import time
import sys
import logging
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import StaleElementReferenceException

from urllib.parse import urlparse
from operator import itemgetter

import pymysql.cursors
from groupon_scraper import groupon_scraper
from livingsocial_scraper import livingsocial_scraper


connection = pymysql.connect(host='localhost',
                             user='root',
                             password='',
                             db='', #
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

try:  # 1. Fetch the live deals from database (select * from deals_tracking where expired = 0)
    with connection.cursor() as cursor:
        # Read a single record
        #sql = "SELECT id, href FROM `deal_detail` WHERE expired = 0"
        sql = "SELECT DISTINCT href, city FROM `deal_detail`"
        cursor.execute(sql)
        href_list = cursor.fetchall() # 	2. Store them into dictionary {deal_id: href} pair.

        print(href_list)
        # 	3. For each item in dictionary:
        for i in href_list:
            href = i['href']
            if 'groupon' in href:
                driver = webdriver.Chrome()
                driver.get(href)
                html = driver.page_source
                groupon_scraper(html, i['city'], 1) # 1 because this is Tracker for deal prices ONLY.
                driver.close()
                driver.quit()
            elif 'livingsocial' in href:
                driver = webdriver.Chrome()
                driver.get(href)
                html = driver.page_source
                livingsocial_scraper(html, i['city'], 1) # 1 because this is Tracker for deal prices ONLY.
                driver.close()
                driver.quit()

except Exception as e:
    print(e)
    pass
finally:
    connection.close()


