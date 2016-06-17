#!/usr/bin/python3
from bs4 import BeautifulSoup
from lxml import html
from datetime import datetime
from datetime import timedelta
from selenium import webdriver
import traceback
import requests
import re
import sys
#import os.path
from sql_miner import sql_miner

city = ""
class groupon_scraper:
	def __init__(self, html, city_name, tracker):
		global city
		city = city_name
		soup = BeautifulSoup(html, "html.parser")
		self.parser(soup, tracker)

	def parser(self, soup, tracker):
		deal_data = {}
		deal_data['alive'] = 0
		# check if title can be scraped.

		href = soup.find("meta",{"property":"og:url"})
		name = None
		if href != None:
			href = href["content"]
			if "https://www.groupon.com/browse" not in href:
				name = soup.find("meta",{"property":"og:title"})["content"]
			if name != None: # if title exists then try to scrape the rest
				deal_data['alive'] = 1
				deal_data['name'] = name
				deal_data['href'] = href
				deal_data['parent_ID'] = 0
				address, short_description, description = "", "", ""
				################################# common chunk ########################################
				try: # descriptions
					short_description = soup.find("meta",{"property":"og:description"})
					if short_description != None:
						short_description = short_description["content"]

					description = soup.find("div", {"itemprop":"description"})
					if description != None:
						description = description.text
				except Exception as e:
					traceback.print_exc()
					pass
				deal_data['short_description'] = short_description
				deal_data['description'] = description

				try: #address tag
					temp_address = soup.find("div", class_="address icon-marker-filled")
					if temp_address != None:
						temp_address = temp_address.text.strip().splitlines()
					address = self.address_handler(temp_address)
				except Exception as e:
					traceback.print_exc()
					pass
				deal_data['address'], deal_data['city'] = address, city

				try: #fine print
					fine_print = soup.find("div", class_="t-pod fine-print ")
					if fine_print != None:
						fine_print = fine_print.get_text()
				except Exception as e:
					traceback.print_exc()
					pass
				deal_data['fine_print'] = fine_print		

				groupon_rating = ""
				try: # groupon rating
					rating = soup.find("meta", itemprop="ratingValue")
					if rating != None:
						rating = rating["content"]
						customer_count = soup.find("meta", itemprop="ratingCount")
						if customer_count != None:
							customer_count = customer_count["content"]
						else:
							customer_count = 0
						groupon_rating = rating + "%% out of " + customer_count + " customers recommended."
				except Exception as e:
					print(e, "no groupon rating")
					pass
				deal_data['groupon_rating'] = groupon_rating
				deal_data['temp_price'], deal_data['yelp_info'] = "","" #livingsocial only , from yipit, uncertain possibility
				deal_data['facebook_count'], deal_data['twitter_count'] = "", ""

				exp_date = soup.find("div", class_="limited-time")
				if exp_date != None:
					try: # Handle Expiry date
						if (exp_date.find("span", {"class":"no-counter"}) != None): # when there is no time set, i.e. "Limited Time Remaining!" 
							exp_date = exp_date.find("span", {"class":"no-counter"}).next
						elif (exp_date.find("ul", {"class":"counter"}) != None): #when there is a counter going on, see below
							temp_list = exp_date.find("ul",{"class":"counter"}).find("li",{"class":"countdown-timer"})
							time = temp_list.text # i.e. 3 days 06:32:35
							## now let's find out the exact expiry date.
							form_time = time.split() #list formatted time

							days = 0
							if len(form_time) > 1:
								days = int(form_time[0])
								hrs = int(form_time[2].split(":")[0])
								mins = int(form_time[2].split(":")[1])
								sec = int(form_time[2].split(":")[2])
							elif len(form_time) == 1:
								hrs = int(form_time[0].split(":")[0])
								mins = int(form_time[0].split(":")[1])
								sec = int(form_time[0].split(":")[2])

							exp_date = datetime.now() + timedelta(hours = days*24 + hrs, minutes = mins, seconds = sec)
							exp_date = exp_date.strftime("%a %b %d, %Y %H:%M:%S")
						else: #when it does not have a time tag.
							exp_date = "Time not found."
					except Exception as e:
						traceback.print_exc()
						pass
				else:
					exp_date = ""
				deal_data['exp_date'] = exp_date
				expired = 0 #time left = "limited time remaining"
				if "Limited" in exp_date:
					expired = 1
				deal_data['expired'] = expired

				########################################################################################
				#
				# Check if it is a multi-option deal or not.
				#
				multi_option = soup.find("ul",{"class":"multi-option-breakout"}) 
				if (multi_option == None):
					######################################################## Single Item ######################################################## 
					deal_data['opt_count'] = 0 #single item
					deal_data['opt_number'] = 0
					orig_price, sale_price, qty_bought, exp_date, fb_count, twitter_count, groupon_rating = "", "", "", "", "", "", ""
					try: # original price
						orig_price = soup.find("td",class_="discount-value")
						if orig_price != None:
							orig_price = orig_price.next # non groupon user pays this
					except Exception as e:
						traceback.print_exc()
						pass
					deal_data['orig_price'] = orig_price

					try: # sale price
						sale_price = soup.find("span",{"class":"price"})
						if sale_price != None:
							sale_price = sale_price.next # groupon price
					except Exception as e:
						traceback.print_exc()
						pass
					deal_data['sale_price'] = sale_price

					try: # quantity bought so far
						qty_bought = soup.find(class_="qty-bought icon-group")
						if qty_bought != None:
							qty_bought = qty_bought.get_text().strip() # qty sold so far
							if "First" in qty_bought: # Be the First to Buy!
								qty_bought = 0
					except Exception as e:
						traceback.print_exc()
						pass
					deal_data['bought_count'] = qty_bought
					
					sold_out = 0 # Cannot find this in single item deal./ NOTE THAT THIS CAN BE CHANGED TO 1 WHEN THE DEAL IS NO LONGER AVAILABLE.
					deal_data['sold_out'] = sold_out

					# SQL insertion.
					if (tracker == 0):
						SQL_worker = sql_miner(deal_data)
						SQL_worker.insert_single()

					SQL_worker = sql_miner(deal_data)
					SQL_worker.insert_single_price()
				
				else:
					######################################################## Multi Options ######################################################## 
					try:
						self.multi_opt_parser(deal_data, multi_option.find_all("li", recursive = False), tracker)
					except Exception as e:
						traceback.print_exc()
						pass

			else: # else the item is un-scrapable
				print("item does not exist")
		
	def multi_opt_parser(self, parent_data, option_list, tracker):
		#################################################### Parent Deal first ################################
		# Precondition : parent_data contains : name, exp_date, description, short_description, fine_print, address, city, href, yelp_info, parentID
		# what does parent deal need now? 
		parent_data['orig_price'] = ""

		parent_data['sale_price'] = ""
		parent_data['bought_count'] = ""
		parent_data['sold_out'] = 0
		parent_data['opt_count'] = len(option_list)
		parent_data['opt_number'] = 0

		if (tracker == 0):
			SQL_worker = sql_miner(parent_data)
			SQL_worker.insert_single()

		##### handling children
		for i in range(len(option_list)):
			opt_data = {}
			option = option_list[i]

			# In Child deals, opt_count is treated as the 'order' / 'option number' of the deal.
			opt_data['opt_number'] = i+1 
			opt_data['opt_count'] = 0

			name = "" #option name
			try: 
				name = option.find("h3")
				if name != None:
					name = name.text
			except Exception as e:
				traceback.print_exc()
				pass
			opt_data['name'] = name
			opt_data['alive'] = 1
			opt_data['href'] = parent_data['href']
			opt_data['exp_date'] = parent_data['exp_date']
			opt_data['expired'] = parent_data['expired']
			opt_data['groupon_rating'] = parent_data['groupon_rating']
			opt_data['city'] = parent_data['city']

			opt_data['short_description'], opt_data['fine_print'], opt_data['facebook_count'], opt_data['twitter_count'] = "", "", "", ""
			opt_data['address'], opt_data['yelp_info'], opt_data['temp_price'] = "", "", ""

			description = "" #option description
			try:
				description = option.find("input").get("data-description")
			except Exception as e:
				traceback.print_exc()
				pass
			opt_data['description'] = description


			orig_price = "" #option original price
			try:
				orig_price = option.find("input").get("data-formatted-value")
			except Exception as e:
				traceback.print_exc()
				pass
			opt_data['orig_price'] = orig_price

			sale_price = "" #option sale price
			try:
				sale_price = option.find("input").get("data-formatted-price")
			except Exception as e:
				traceback.print_exc()
				pass
			opt_data['sale_price'] = sale_price

			qty_bought = ""
			try:
				qty_bought = option.find("input").get("data-sold-message")
			except Exception as e:
				traceback.print_exc()
				pass
			opt_data['bought_count'] = qty_bought

			status = 0
			try:
				status_text = option.find("p", class_ = "status")
				if status_text != None:
					status_text = status_text.text.strip()
					if 'Sold' in status_text:
						status = 1
			except Exception as e:
				traceback.print_exc()
				pass
			opt_data['sold_out'] = status

			if (tracker == 0):
				SQL_worker = sql_miner(opt_data)
				SQL_worker.insert_option()

			SQL_worker = sql_miner(opt_data)
			SQL_worker.insert_option_price()


	def address_handler(self, temp_address):
		container = []
		address = ""
		if (temp_address != None):
			for i in temp_address: # The address seems to be a bit tweaky (has two forms so far)
				if i.strip() != "":
					container.append(i.strip())
			# now handle exceptional cases of output/scraped html address tag format
			for i in range(len(container)-1): # tested only for canadian
				if container[i+1].startswith(","):
					temp_address = container[i] + container[i+1] # because it"s always next to each other for street + postal code
				else:
					temp_address = container[i] + ", " + container[i+1]
				if re.search("[ABCEGHJKLMNPRSTVXY][0-9][ABCEGHJKLMNPRSTVWXYZ] ?[0-9][ABCEGHJKLMNPRSTVWXYZ][0-9]", \
					temp_address , re.IGNORECASE | re.DOTALL):
					container = temp_address
					break; #break this for loop at first search.
			try:
				address = container.split()
				if "+" in address[-1]:
					address = address[:-1]
				address = " ".join(" ".join(address).split(","))
			except Exception as e:
				pass
			if address == "": # then american address
				address = " ".join(container)

		return address

###################### testing chunk is below RUN #################################
"""
driver = webdriver.Chrome()
driver.get("https://www.groupon.com/deals/gl-symphony-in-the-gardens") # multi
html = driver.page_source
groupon_scraper(html, "toronto", 0)
#driver.close()
#driver.quit()
"""