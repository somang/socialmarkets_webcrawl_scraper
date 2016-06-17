#!/usr/bin/python3
from bs4 import BeautifulSoup
from lxml import html
from datetime import datetime
from datetime import timedelta
import sys
import re
import requests
from selenium import webdriver
from sql_miner import sql_miner

city = ""
class livingsocial_scraper:
	def __init__(self, html, city_name, tracker):
		#print("scraping the groupon deal.")
		global city
		city = city_name
		soup = BeautifulSoup(html, "html.parser")
		self.parser(soup, tracker)

	def parser(self, soup, tracker):
		deal_data = {}		
		deal_data['expired'] = 1
		deal_data['alive'] = 1

		dealoveralert = soup.find("div", {"id":"deal-over-alert"})
		if dealoveralert != None:
			deal_data['alive'] = 0
			deal_data['expired'] = 0
			
		# check if title can be scraped.
		href = soup.find("meta",{"property":"og:url"})
		if href != None:
			href = href["content"]

			name = soup.find("meta",{"property":"og:title"})
			if name != None:
				name = name["content"]

			description = soup.find("div", itemprop="description")
			if description != None:
				try:
					description = description.text
				except Exception as e:
					print(e)
					pass

			short_description = soup.find("meta", {"name":"description"})
			if short_description != None:
				try:
					short_description = short_description["content"]
				except Exception as e:
					print(e)
					pass

			urgency_price = soup.find("p", {"id":"urgency-price"})
			try:
				if urgency_price != None:
					urgency_price = urgency_price.text
			except Exception as e:
				print(e)
				pass

			#sale price, original price
			sale_price, orig_price = 0, 0
			dealbox = soup.find("ul", {"class":"unstyled ls-price_info ls-large_value"})
			if dealbox != None:
				multiprice = dealbox.find_all("li", recursive = False)
				if multiprice != None:
					option = multiprice[0].text
					prices = self.digit_sum(option)
					sale_price = prices[0]
					if len(prices) > 1:
						if ',' in prices[1]:
							prices[1] = self.convert_numb(prices[1])
						if '$' in prices[1]:
							prices[1] = prices[1].split("$")[1]
						try:
							orig_price = float(prices[0].split("$")[1]) + float(prices[1])			
						except Exception as e:
							print(e)
							pass
				else:
					singleprice = dealbox.find("li", class_="ls-original_price")
					#print("single price?", singleprice)
			else:
				dealbox = soup.find("div", class_="price-info")
				if dealbox != None:
					retail = dealbox.find("p", class_="retail-price")
					if retail != None:
						orig_price = retail.text.split()[0]
					sale_price = soup.find("b", {"itemprop":"lowprice"})
					if sale_price != None:
						sale_price = sale_price.text

			#savings = soup.find("p", class_="savings")
			#if savings != None:
			#	savings = savings.text.split()[1]
			#print(savings)

			#number sold
			bought_count = soup.find("div", class_="purchased")
			if bought_count != None:
				tmp_bcount = bought_count.find("span", class_="value")
				if tmp_bcount != None:
					bought_count = tmp_bcount.text
			else:
				bc_list = soup.find("ul", {"id":"stats_deal_list"})
				bc_list = bc_list.find("li", {"id":"deal-purchase-count"})
				bought_count = bc_list.text.split()[0]

			#fine print
			fine_print = soup.find("div", class_="fine-print")
			if fine_print != None:
				fine_print = fine_print.text
			else:
				fine_print = soup.find("section", class_="fine-print")
				if fine_print != None:
					fine_print = fine_print.text

			#social networks
			social_networks = soup.find("ul",{"class":"unstyled share-links"})
			facebook_count, twitter_count = "" , ""
			if social_networks != None:
				sn_list = social_networks.find_all("li", recursive = False)
				if len(sn_list) == 3:
					facebook_count = sn_list[0].find("span", class_="share-count")
					if facebook_count != None:
						facebook_count = facebook_count.text
					twitter_count = sn_list[1].find("span", class_="share-count")
					if twitter_count != None:
						twitter_count = twitter_count.text
			else:
				social_networks = soup.find("ul", {"class":"share-links"})
				if social_networks != None:
					sn_list = social_networks.find_all("li", recursive = False)
					if len(sn_list) == 3:
						facebook_count = sn_list[0].find("span", class_="share-count")
						if facebook_count != None:
							facebook_count = facebook_count.text
						twitter_count = sn_list[1].find("span", class_="share-count")
						if twitter_count != None:
							twitter_count = twitter_count.text

			#rating
			rating = soup.find("div", class_="recommend")
			if rating != None:
				rating = rating.text
			
			#address
			address = soup.find("span", itemprop="address")
			if address != None:
				address = self.address_handler(address)
			else:
				t = soup.find("address", class_="vcard")
				if t != None:
					address = self.address_handler(t)
				else:
					address = ""

			deal_data['name'] = name
			deal_data['exp_date'] = ""
			deal_data['orig_price'] = orig_price
			deal_data['sale_price'] = sale_price
			deal_data['description'] = description
			deal_data['short_description'] = short_description
			deal_data['fine_print'] = fine_print
			deal_data['address'] = address
			deal_data['city'], deal_data['href'] = city, href
			deal_data['yelp_info'] = ""
			deal_data['opt_count'], deal_data['opt_number'] = 0, 0
			deal_data['parent_ID'] = 0
			deal_data['bought_count'] = bought_count
			deal_data['temp_price'] = urgency_price
			deal_data['groupon_rating'] = rating
			deal_data['facebook_count'] = facebook_count
			deal_data['twitter_count'] = twitter_count
			deal_data['sold_out'] = 0
			
		# SQL insertion.
		if (tracker == 0):
			SQL_worker = sql_miner(deal_data)
			SQL_worker.insert_single()

		SQL_worker = sql_miner(deal_data)
		SQL_worker.insert_single_price()

	
	def digit_sum(self, str_price):
		return [i for i in str_price.split() if "$" in i]

	def convert_numb(self, str_price):
		t = ""
		temp = str_price.split(".") #check if there are any cents unit.
		for d in temp[0]:
			if d.isdigit():
				t+=d
		if len(temp) > 1:
			t+=temp[1]
		return t

	def address_handler(self, address):
		ta = ""
		p = address.find_all("meta", recursive = False)
		for i in p:
			ta += i["content"] + " "
		return ta