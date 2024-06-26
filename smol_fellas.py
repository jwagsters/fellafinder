import importlib, base64, functools, pickle, operator
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from pathlib import Path
from urllib import request
from urllib.request import Request, urlopen
from PIL import Image
from io import BytesIO
import time, datetime, csv, re, requests, sys, os, random, json, hashlib

from selenium import webdriver 
from selenium.webdriver.chrome.options import Options 


options = webdriver.ChromeOptions() 
# Suppress the error messages/logs
options.add_experimental_option('excludeSwitches', ['enable-logging'])

# You need to point this to wherever your Chromedriver is located
DRIVER_PATH = '/'
driver = webdriver.Chrome(options=options)

print = functools.partial(print, flush=True)

# You can set default username and password here
USER_NAME = ""
PASSWORD = ""

fella_dict = {}
smol_limit = 500		# Fellas with more than this amount of followers are not considered smol 
session_count = 0



def main():
	global USER_NAME, PASSWORD, fella_dict

	fella_dict = loadFellas()
	
	if len(sys.argv) > 2:
		USER_NAME = sys.argv[1]
		PASSWORD = sys.argv[2]

	if not USER_NAME or not PASSWORD:
		print("You must supply a username and password to log in to xhitter")
		print("Syntax: python smol_fellas.py username password")
		quit()

	print("\n\n\n****** LET'S GO FIND SOME SMOL FELLAS! ******")

	print("\nUsername: " + USER_NAME)
	print("Password: ********")
	
	login(USER_NAME, PASSWORD)

	print_stats()

	run()



def run():

	global session_count
	
	while True:

		# Run a session
		session_count += 1
		print("\n\nSESSION " + str(session_count))
		session()
		print_stats()
		driver_get("https://x.com/" + USER_NAME)

		if random.random() < 0.3 or datetime.datetime.now().isoweekday() == 5:
			post_message(output_string())
			follow_back()
		sleep_rand(60*30, True)


def session():


	fellas_by_checked = sorted(fella_dict, key = lambda item: fella_dict[item]['checked'])
	fellas_by_scraped = sorted(fella_dict, key = lambda item: fella_dict[item]['scraped'])

	time.sleep(30)

	check_list = []
	for fella in fellas_by_checked:
		if fella_dict[fella]['follower_count'] < smol_limit and not fella_dict[fella]['ignore']:
			check_list.append(fella)

	scrape_list = []
	for fella in fellas_by_scraped:
		if not fella_dict[fella]['ignore']:
			scrape_list.append(fella)


	for i in range(1, random.randint(15,30)):
		print("\n" + str(i) + ": ", end="")
		if i%2 == 0:
			visit_fella(check_list.pop(0))
		else:
			pass
			#scrape_fella(scrape_list.pop(0))

		saveFellas()
		sleep_rand(120)



def scrape_fella(fella):
	print(fella)
	print("Scraping @" + fella)

	ls = (datetime.datetime.now() - fella_dict[fella]["scraped"]).days
	if ls > 365:
		print ("Last scraped: never")
	else:
		print(f"Last scraped: {ls} days ago")

	body_text = driver_get("https://x.com/" + fella)

	if "These posts are protected" in body_text or "Account suspended" in body_text or "You’re blocked" in body_text or "This account doesn’t exist" in body_text:
		fella_dict[fella]['ignore'] = True 
		print("Account unavailable. Added to ignore list.")
		return

	try:
		driver.find_element(By.CSS_SELECTOR, "div[aria-label='Follow @" + fella + "']").click()
		print("Followed @" + fella)
		sleep_rand(3)
	except:
		pass

	body_text = driver_get("https://x.com/" + fella + "/followers")
	insertStyle()


	index = 0
	exception_count = 0
	done_list = []

	while True:
		followers = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='cellInnerDiv']")
		for follower in followers:

			try:
				follower.text 
			except:
				break

			if follower.text == "": # There's always an empty container at the bottom of the list
				print()
				fella_dict[fella]['scraped'] = datetime.datetime.now()
				return

			index += 1
			if index % 200 == 0:
				saveFellas()

			link = follower.find_element(By.CSS_SELECTOR, "a")
			user = link.get_attribute('href').replace("https://x.com/", "")
			if user in done_list:
				continue


			try:
				driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center', inline: 'nearest'})", follower)
				time.sleep(0.5)
				sleep_rand(0.5)			
				if user in fella_dict and (datetime.datetime.now() - fella_dict[user]['checked']).days < 7:
					driver.execute_script("arguments[0].setAttribute('scraped', 'true')", follower)
					if fella_dict[user]['follower_count'] < smol_limit:
						driver.execute_script("arguments[0].setAttribute('fellatype', 'smol')", follower)
						print("s", end="")
					else:
						driver.execute_script("arguments[0].setAttribute('fellatype', 'large')", follower)
						print("f", end="")
					done_list.append(user)
					continue
			
				txt = follower.text.lower()


				if ("nafo " in txt or "fella" in txt or "fellina" in txt or "bonk" in txt) and (user not in block_list()):

					# It's just a jump to the left...
					ActionChains(driver).move_to_element(link).perform()
					time.sleep(1.2)

					hovercard = driver.find_element(By.CSS_SELECTOR, "div[data-testid='HoverCard']")
					for link in hovercard.find_elements(By.CSS_SELECTOR, "a"):
						if link.text[-9:] == "Following":
							following_count = int(link.text.replace(" Following", "").replace("K", "000").replace(".", "").replace(",", ""))
						if link.text[-9:] == "Followers":
							follower_count = int(link.text.replace(" Followers", "").replace("K", "000").replace(".", "").replace(",", ""))

					if follower_count < smol_limit:
						print("S", end="")
						driver.execute_script("arguments[0].setAttribute('fellatype', 'smol')", follower)
						try:
							driver.find_element(By.CSS_SELECTOR, "div[aria-label='Follow @" + user + "']").click()
						except:
							pass
						time.sleep(1)
					else:
						print("F", end="")
						driver.execute_script("arguments[0].setAttribute('fellatype', 'large')", follower)

					if user not in fella_dict:
						fella_dict[user] = get_new_fella(user, following_count, follower_count)
					else:
						fella_dict[user]["following_count"] = following_count
						fella_dict[user]["follower_count"] = follower_count
						fella_dict[user]["checked"] = datetime.datetime.now()

				else:
					print(".", end="")

				# ...and then a step to the riiiight
				ActionChains(driver).move_to_element_with_offset(link, 600, 0).perform()

				driver.execute_script("arguments[0].setAttribute('scraped', 'true')", follower)

			except Exception as e:
				exception_count += 1
				print("-", end="")
				time.sleep(10)
			done_list.append(user)



def visit_fella(fella):

	print("Visiting @" + fella)

	lc = (datetime.datetime.now() - fella_dict[fella]["checked"]).days
	print(f"Last checked: {lc} days ago")

	body_text = driver_get("https://x.com/" + fella)
	time.sleep(3)

	tweets = driver.find_elements(By.CSS_SELECTOR, "article[data-testid='tweet']")

	if "These posts are protected" in body_text or "Account suspended" in body_text or "You’re blocked" in body_text or "This account doesn’t exist" in body_text:
		fella_dict[fella]['ignore'] = True 
		print("Account unavailable. Added to ignore list.")
		return


	driver_get("https://x.com/" + fella + "/with_replies")
	time.sleep(3)
	last_reply = most_recent()
	driver_get("https://x.com/" + fella)
	last_tweet = most_recent()
	fella_dict[fella]["last_active"] = last_tweet if last_tweet > last_reply else last_reply


	la = (datetime.datetime.now() - fella_dict[fella]["last_active"]).days
	print(f"Last active: {la} days ago")

	if la > 60:
		fella_dict[fella]['ignore'] = True
		print("Added to ignore list")
		return

	if la < 7:
		boost_fella(fella)

	check_fella(fella)
	
	time.sleep(3)



def check_fella(fella):
	body_text = driver.find_element(By.CSS_SELECTOR, "body").text
		
	followers_link = driver.find_element(By.CSS_SELECTOR, "a[href='/" + fella + "/verified_followers']")
	follower_count = int(followers_link.find_element(By.CSS_SELECTOR, "span:first-child > span").text.replace("K", "000").replace(".", "").replace(",", ""))
	following_link = driver.find_element(By.CSS_SELECTOR, "a[href='/" + fella + "/following']")
	following_count = int(following_link.find_element(By.CSS_SELECTOR, "span:first-child > span").text.replace("K", "000").replace(".", "").replace(",", ""))

	update_fella(fella_dict[fella], follower_count, following_count, True)		

	fella_dict[fella]["checked"] = datetime.datetime.now()



def update_fella(fella, follower_count, following_count, log = False):
	if log:
		print("Followers then: " + str(fella["follower_count"]) + " | Followers now: " + str(follower_count))
	if fella['follower_count'] < 500: 
		if follower_count >= 500:
			exclamations = ["WHOOP!!!", "HUZZAH!!!", "HOORAY!!!", "YAY!!!", "YIPPEE!!", "WORD UP!"]
			message =  random.choice(exclamations) + " @" + fella['username'] + " now has " + str(follower_count) + " followers and is no longer a smol fella! "
			message += "Thanks fellas for your support and please look after them. \n\n@" + fella['username'] + " please remember to check your followers list and follow everyone back. (Slowly, so you don't get locked.)"
			post_message(message)
		else:
			try:
				driver.find_element(By.CSS_SELECTOR, 'div[data-testid="userFollowIndicator"]')
			except:
				days_unreciprocated = (datetime.datetime.now() - fella['found']).days
				print("Not following back after " + str(days_unreciprocated) + " days")


				if days_unreciprocated > 30:
					
					fella['ignore'] = True
					print("Ignored.")
					try:
						time.sleep(2)
						driver.find_element(By.CSS_SELECTOR, 'div[aria-label="Following @' + fella['username'] + '"]').click()
						time.sleep(2)
						driver.find_element(By.CSS_SELECTOR, 'div[data-testid="confirmationSheetConfirm"]').click()
						time.sleep(2)
						print("Unfollowed.")
					except:
						print("Failed to unfollow.")
						pass
				
				elif days_unreciprocated > 14:
					message = "@" + fella['username'] + " - following back is kind and good. Don't forget to check your followers list and follow them back.\n\n"
					message += "https://x.com/" + fella['username'] + "/followers \n\nThanks!" 
					post_message(message)

	 
	fella["following_count"] = following_count
	fella["follower_count"] = follower_count



def boost_fella(fella):

	try:
		driver.find_element(By.CSS_SELECTOR, "div[aria-label='Follow @" + fella + "']").click()
		print("Followed @" + fella)
		sleep_rand(3)
	except:
		pass

	tweets = driver.find_elements(By.CSS_SELECTOR, "article[data-testid='tweet']")
	if len(tweets):
		tweet = random.choice(tweets)
		try:
			rt_btn = tweet.find_element(By.CSS_SELECTOR, "div[data-testid='retweet']")
		except:
			rt_btn = None
		try:
			like_btn = tweet.find_element(By.CSS_SELECTOR, "div[data-testid='like']")
		except:
			like_btn = None

		driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center', inline: 'nearest'})", tweet)
	
	sleep_rand(1)

	if random.random() < 0.5 and like_btn:
		try:
			print("Like tweet: ", end="")
			like_btn.click()
			time.sleep(1)
			print("success")
		except:
			print("failed")

	if random.random() < 0.1 and rt_btn:
		try:
			print("Retweet: ", end="")
			rt_btn.click()
			time.sleep(1)
			driver.find_element(By.CSS_SELECTOR, "div[data-testid='Dropdown'] div[data-testid='retweetConfirm']").click()
			sleep_rand(3)
			print("success")
		except:
			print("failed")
	return



def post_message(content):
	time.sleep(3)
	button_click("a[data-testid='SideNav_NewTweet_Button']")
	time.sleep(2)
	input_field = driver.find_element(By.CSS_SELECTOR, "div[aria-modal='true'] [data-text='true']")
	input_field.send_keys(Keys.CONTROL + "a")
	input_field.send_keys(content)
	time.sleep(20)
	tweet_btn = get_button_by_text("Post")
	driver.execute_script("arguments[0].click()", tweet_btn)
	print("\n\n--- Tweet Sent at " + datetime.datetime.now().strftime("%H:%M") + " ---\n")
	print(content)
	print("\n---------------------------- \n")
	time.sleep(5)



def most_recent():
	time_els = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='User-Name'] time")
	most_recent = datetime.datetime.fromtimestamp(0)
	for time_el in time_els:
		date = time_el.get_attribute("datetime").split("T")[0].split("-")
		year = int(date[0])
		month = int(date[1])
		day = int(date[2])
		d = datetime.datetime(year, month, day)
		most_recent = d if d > most_recent else most_recent
	return most_recent



def sleep_rand(t, log=False):
	r = random.random() - 0.5
	if log:
		print(f"Pausing for " + str(datetime.timedelta(seconds=int(t+t*r))), flush=True)
		print(f"Resuming at " + (datetime.timedelta(seconds=int(t+t*r)) + datetime.datetime.now()).strftime("%H:%M:%S"), flush=True)
	time.sleep( t+t*r )



def login(username, password):
	sleep_rand(1)
	driver_get("https://x.com/i/flow/login")
	sleep_rand(8)
	driver.find_element(By.CSS_SELECTOR, "input").send_keys(username)
	sleep_rand(2)
	get_button_by_text("Next").click()
	time.sleep(8)
	driver.find_element(By.CSS_SELECTOR, "input[name='password']").send_keys(password)
	sleep_rand(2)
	get_button_by_text("Log in").click()
	time.sleep(5)



def output_string():

	tweet_list = []

	fellas_by_checked = sorted(fella_dict, key = lambda item: fella_dict[item]['checked'], reverse = True)
	for fella in fellas_by_checked:
		f = fella_dict[fella]
		now = datetime.datetime.now()
		if f['last_active'] != None and (now - f['last_active']).days < 14 and not f['ignore'] and f['follower_count'] < smol_limit:
			tweet_list.append(fella)

	str1 = ["More excellent fellas", "More smol fellas here", "Here are some little fellas", "These are smol fellas", "Here's some lesser-known fellas"]
	s1 = random.choice(str1)
	str2 = [" with not many followers of their own. ", " who need a bit of NAFO love. ", " who need your follows. ", " for you to help. ", " so you can follow and boost. ", " who need your support. "]
	s2 = random.choice(str2)
	str3 = ["Go give them a hand!", "Following is the way.", "See a smol fella, follow a smol fella!", "You know the drill.", "#NAFOExpansionIsNonNegotiable."]
	s3 = random.choice(str3)
	ostr = s1 + s2 + s3 + "\n\n"

	str4 = ["*Don't forget - check your followers and follow them back", "*Following back is kind and good.", "*Got followed?  Follow back.", "*Do your own due diligence please", "*Always double-check accounts before following", "*Dr NAFO says: 'Check who you follow!'", "*Dr NAFO says: 'Always follow back!'"]
	s4 = '\n' + random.choice(str4)
	s5 = "\n\n#nafo #smolfellas"

	while True:
		fella = tweet_list.pop(0)
		fella_str = "@" + fella + " - " + str(fella_dict[fella]['follower_count']) + "\n"
		if len(ostr + fella_str + s4 + s5) < 280:
			ostr += fella_str
			fella_dict[fella]['tweeted'] = datetime.datetime.now()
		else: 
			break
	ostr += s4 + s5
	saveFellas()
	return ostr



def sign_off():
	smol_fella_count = len(get_smol_fellas())
	message = "Good night all.\n\n"
	message += "I am currently tracking " + str(smol_fella_count) + " smol fellas. "
	message += "Let's make them all into big fellas!\n\n"
	message += "Find them all here: #smolfellas"
	return message



def loadFellas():

	global fella_dict

	if os.path.exists("fellas.pkl"):
		with open('fellas.pkl', 'rb') as f:
			fella_dict = pickle.load(f)
			clean_list()
			validate_fellas()
			return fella_dict
	else:
		print("fellas.pkl not found!")
		quit()



def saveFellas():
	clean_list()
	with open('fellas.pkl', 'wb') as f:
		pickle.dump(fella_dict, f)
	with open('fellas.pkl.bak', 'wb') as f:
		pickle.dump(fella_dict, f)
	print("Saved " + str(len(fella_dict)) + " fellas")



def validate_fellas():

	for fella in fella_dict:

		if not "last_active" in fella_dict[fella]: 
			fella_dict[fella]["last_active"] = datetime.datetime.now()
		if fella_dict[fella]["checked"] == None:
			fella_dict[fella]["checked"] = datetime.datetime.fromtimestamp(0)


		if fella in block_list():
			fella_dict[fella]["ignore"] = True
		for term in block_patterns():
			if term in fella:
				fella_dict[fella]["ignore"] = True

	for fella in add_list():
		if fella not in fella_dict:
			fella_dict[fella] = get_new_fella(fella)
			print("Added", fella)



	print ("\n\nValidated fella data")



def insertStyle():

	styleScript = """
	let styleEl = document.createElement("style")
	styleEl.type = 'text/css'
	styleEl.innerHTML = "div[data-testid='cellInnerDiv']{border-left: solid 5px #333} div[scraped='true']{border-left: solid 5px #bbb} div[scraped='true'][fellatype='smol']{border-left: solid 5px #ffd700} div[scraped='true'][fellatype='large']{border-left: solid 5px #0057b8}"
	console.dir(styleEl)
	document.head.appendChild(styleEl)
	"""

	driver.execute_script(styleScript)



def print_stats():
	smol_count = 0
	big_count = 0
	scraped_count = 0
	ignore_count = 0
	with open("smolfellas.txt", "w") as file:
		for fella in fella_dict:
			if fella_dict[fella]['ignore']:
				ignore_count += 1
				continue
			if (datetime.datetime.now() - fella_dict[fella]['scraped']).days < 365:
				scraped_count += 1
			if fella_dict[fella]['follower_count'] < smol_limit:
				smol_count += 1
				file.write("@" + fella + " - " + str(fella_dict[fella]['follower_count']) + "\n")
			else:
				big_count += 1
	print()
	print("Fellas:      " + str(len(fella_dict)))
	print("Big fellas:  " + str(big_count))
	print("Smol fellas: " + str(smol_count))
	print("Scraped:     " + str(scraped_count))
	print("Ignoring:    " + str(ignore_count))



def clean_list():

	for b in block_list():
		if b in fella_dict:
			fella_dict[b]['ignore'] = True

	for b in block_patterns():
		for f in fella_dict:
			if b.lower() in f.lower():
				fella_dict[f]['ignore'] = True



def driver_get(url):

	global session_count, driver, USER_NAME, PASSWORD

	print("Getting: " + url)

	if datetime.datetime.now().hour < 6:
		post_message(sign_off())
		print("It's time for bed.")
		time.sleep(60*60*7)
		session_count = 0
		prune_following()
		follow_back()

	try:
		driver.get(url)
	except:
		print("Problem loading page " + url)
		try:
			print("Restarting browser.")
			driver.close()
			driver = webdriver.Chrome(options=options)
			login()
			driver.get(url)
		except Exception as e:
			print("Failed to restart browser")
			print(e)
			quit()


	time.sleep(3)
	body_text = driver.find_element(By.CSS_SELECTOR, "body").text


	if "Your account has been locked" in body_text:
		print("They're on to us!  Time for an Arkose.  Press Enter when account unlocked.")
		input()


	if "Something went wrong. Try reloading" in body_text or body_text == "":
		print("Rate limited.  Need to wait a bit.")
		current_url = driver.current_url
		driver.close()
		sleep_rand(2*60*60, True)
		driver = webdriver.Chrome(options=options)
		driver_get(current_url)
		time.sleep(3)


	try:
		get_button_by_text("Accept all cookies").click()	
		sleep_rand(5)
	except:
		pass

	print("Got: " + url)

	return body_text



def follow_back():
	driver_get("https://x.com/" + USER_NAME + "/followers")
	time.sleep(3)
	done_list = []
	follow_limit = 25
	follow_count = 0
	follower_count = 0
	follower_limit = 200
	while True:
		followers = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='cellInnerDiv']")
		for follower in followers:
			try:
				if follower.text == "":
					print("Checked " + str(follower_count) + " followers and followed " + str(follow_count) + " back")
					return
				link = follower.find_element(By.CSS_SELECTOR, "a")
				user = link.get_attribute('href').replace("https://x.com/", "")
			except:
				continue
			if user not in done_list:
				follower_count += 1
				driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center', inline: 'nearest'})", follower)
				sleep_rand(0.3)
				try:
					follower.find_element(By.CSS_SELECTOR, 'div[aria-label="Follow @' + user + '"]').click()
					follow_count += 1
					sleep_rand(5)
				except Exception as e:
					pass
				done_list.append(user)
				if follow_count >= follow_limit or follower_count >= follower_limit:
					print("Checked " + str(follower_count) + " followers and followed " + str(follow_count) + " back")
					return

def prune_following():
	print("Pruning follow list")
	driver_get("https://x.com/" + USER_NAME + "/following")
	time.sleep(3)
	done_list = []
	unfollow_limit = 50
	list_item_count = 0
	unfollow_count = 0
	start_unfollowing_at = 500
	while True:
		user_els = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='cellInnerDiv']")
		for user_el in user_els:
			try:
				if user_el.text == "":
					print("Checked " + str(list_item_count) + " followers and unfollowed " + str(unfollow_count))
					return
				link = user_el.find_element(By.CSS_SELECTOR, "a")
				user = link.get_attribute('href').replace("https://x.com/", "")
			except Exception as e:
				continue
			if user not in done_list:
				list_item_count += 1
				driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center', inline: 'nearest'})", user_el)
				sleep_rand(0.2)
				if not "Follows you" in user_el.text and list_item_count > start_unfollowing_at:
					try:
						user_el.find_element(By.CSS_SELECTOR, 'div[aria-label="Following @' + user + '"]').click()
						time.sleep(1)
						driver.find_element(By.CSS_SELECTOR, 'div[data-testid="confirmationSheetConfirm"]').click()
						unfollow_count += 1
						print("x", end="")
						sleep_rand(5)
					except Exception as e:
						print("-", end="")
						pass
				else:
					print(".", end="")
				done_list.append(user)
				if unfollow_count >= unfollow_limit:
					print("Checked " + str(list_item_count) + " followers and unfollowed " + str(unfollow_count))
					return
	
def get_new_fella(username, following_count = 0, follower_count = 0):
	return {
				"username": username,
				"following_count": following_count,
				"follower_count": follower_count,
				"found": datetime.datetime.now(),
				"checked": datetime.datetime.fromtimestamp(0),
				"vetted": False,
				"scraped": datetime.datetime.fromtimestamp(0),
				"tweeted": datetime.datetime.fromtimestamp(0),
				"last_active": None,
				"ignore": False
			}



def get_smol_fellas():
	smol_fella_dict = {}
	for fella in fella_dict:
		if fella_dict[fella]['follower_count'] < smol_limit and not fella_dict[fella]['ignore']:
			smol_fella_dict[fella] = fella_dict[fella]
	return smol_fella_dict



def get_link_containing(url_fragment):
	for el in driver.find_elements(By.CSS_SELECTOR, "a"):
		if url_fragment in el.get_attribute("href"):
			return el



def get_button_by_text(text):
	for el in driver.find_elements(By.CSS_SELECTOR, "button"):
		if text == el.text:
			return el

def button_click(selector):
	button = driver.find_element(By.CSS_SELECTOR, selector)
	driver.execute_script("arguments[0].click()", button)



def add_list():
	return[
		"NAFOwaldviertel",
		"mitchbeatty5"
	]



def block_patterns():
	return [
		"TimDobson",
		"IncelFella",
		"Olena",
		"Schizo"
	]


# Do NOT use this list to find vatniks.  Some are fellas who have requested not to be promoted.
def block_list():
	return [
		"BestActualFella",
		"FellasBot1",
		"RGheitica",	
		"Rikhard_6790",
		"FellaBackUp",
		"olena_ivanenko",
		"waldviertel4Eva",
		"YuliaUaUltra",
		"NastishkaA32359",
		"squeaky1149",
		"AlphariusFella",
		"LuborKonicek",
		"darthrevan1609",
		"ComeCryHereNazi",
		"Regiscarbone",
		"RusselltheAFU",
		"3rdcoming10",
		"Onlyfabs4u2",
		"markusdresch",
		"SarahAshtonL",
		"TimDobson841518",
		"666GeorgeSoros",
		"LeonPidrilov",
		"BSneglar",
		"ukrainiansquad",
		"LazyFella4Ukr",
		"MI6Fella",
		"YevhenKononenko",
		"HargTimes",
		"wcolacola",
		"DirleFella",
		"dimefan099",
		"AussieInRussia",
		"Jonesthaguy",
		"donyogenes",
		"spidivagon",
		"SSfella1488",
		"EthnicNEET",
		"ApfelTot",
		"AndyTheFella",
		"Dauntfella",
		"nafolittledog",
		"PGBlue1878",
		"awanq22",
		"Olliewildwings",
		"politisch",
		"StalinFella",
		"IAmYourNextGen",
		"NAFOSuicideHotL",
		"defensefella",
		"NAFO140701",
		"grndmstrfesxh",
		"RicoDubois",
		"bopandy1_",
		"UnforgivenFella",
		"mykolapastux",
		"premstaller",
		"vatniksoup",
		"Yanazavod",
		"zeinlastweek",
		"Alex_NAFO_UKR",
		"UkrainePetscar",
		"_Antondymtro",
		"_Bondarenk34",
		"_dennis0011",
		"_drepeterypete_",
		"_ivanpanilov",
		"_stop_Russia",
		"11Andriy_koval",
		"12356Ovolodymr",
		"1Andriybohdan",
		"747Antonova",
		"a_dymtro",
		"Adamovich_1",
		"ADanyloboyko",
		"ADorokhov56765",
		"ADymtro7796",
		"AidWorldpeace",
		"AinaobaP52593",
		"Ajani225",
		"aleksander246",
		"aleksander32",
		"AleksanderIvan0",
		"Aleksandermykol",
		"Aleksandra_iv1",
		"Aleksandra31872",
		"AlexanderAndryy",
		"alexanderbrigg",
		"alexbohuslava",
		"AlexGorgealex6",
		"alexphin209",
		"AlexRashchuk",
		"Alexsendral_UK",
		"Alikhanpy12",
		"AlympiyaChowdh1",
		"Anastasia22145",
		"anastasiya979",
		"Andersonmill474",
		"Andrei_maksym",
		"AndreiBess9",
		"Andrew695785",
		"AndreyLvan33976",
		"andrichanto",
		"AndrichKoval",
		"Andriy__Taras",
		"Andriy_1Oleksiy",
		"andriy_bonder",
		"Andriy_shenko",
		"Andriy022",
		"AndriyBohuslav1",
		"AndriyChovnyk",
		"AndriyDmyt2",
		"AndriyDmytro479",
		"Andriydovz1989",
		"Andriyegor",
		"AndriyFedi55043",
		"AndriyI8446",
		"andriymatviy_20",
		"AndriyMatviyko",
		"andriymaxi84457",
		"AndriyMykyta",
		"AndriyOle",
		"AndriyOlek83736",
		"Andriypetro",
		"AndriySama36695",
		"AndriySama54049",
		"Andriysch",
		"Andriyshev97217",
		"Andriyshevchu_k",
		"AndriyTaras02",
		"andriyvolo",
		"AndriyVoskresee",
		"AndriyZelenko",
		"AndryFedir52164",
		"anest92",
		"Aneta_Petrova90",
		"Anetamyk02",
		"Animal_shelter0",
		"Animal_ShelterU",
		"AnimalNafo",
		"ANIMALS_OF_UA",
		"anizalokaloka",
		"ANKURTRIPATHI54",
		"anna_joel41",
		"Annabondar61019",
		"annacbotta",
		"anno1540",
		"anothai_95",
		"AntinShevchenk",
		"Anton_Ivan1990",
		"Anton6226797002",
		"AntonBogdan77",
		"Antonbory11",
		"antonboryslav",
		"AntonioBru53278",
		"antonovapetro",
		"Antonvasyl_",
		"Antonyshevchenk",
		"Ares_toyu",
		"ArkhipMordvinov",
		"Artem_1Marko",
		"Artem_Danylo",
		"artem_dovzhenko",
		"artem_mykhailo",
		"Artem06200",
		"Artem1418089",
		"ArtemAndriy22",
		"ArtemBohdan5",
		"Artemisai0",
		"ArtemOleks78423",
		"ArtemV014",
		"ArtionDmit64807",
		"ArturBohuslavv",
		"AshtonDebb90697",
		"audreywts",
		"austin_teigen",
		"austindumass",
		"AyibadoubraP",
		"b_leo101",
		"Balak278844",
		"BalakSlavi35029",
		"Bandit_Reports",
		"BartoshMaxim",
		"beast_0112",
		"Beccahashing",
		"Berislav18285",
		"Berlins63988Ka",
		"BhodanD",
		"Biggest_Eragon",
		"BigZ1800",
		"billyrogerlife",
		"BilykGeorge",
		"Blackbl93808524",
		"BodaJamesfight",
		"bodashka__dan",
		"Bodashka333",
		"Bogdan_mykailo",
		"Bohdam_Lesh",
		"Bohdan_11937",
		"Bohdan_arten",
		"Bohdan_bondare",
		"Bohdan40",
		"bohdan7991",
		"Bohdana4666",
		"BohdanaAle70044",
		"BohdanAlekseev",
		"Bohdanamatvy",
		"BohdanDanylo277",
		"BohdanIvan009",
		"BohdanIvan17289",
		"BohdanIvan24",
		"Bohdankopakvasy",
		"BohdankoTaras",
		"bohdanoleksiy1",
		"Bohk_",
		"bohuslav_o",
		"Bohuslav309",
		"BohuslavFa76346",
		"Bohuslavp0001",
		"Bohuslavyuriy",
		"bondah_andriy",
		"Borys1477",
		"BorysAndrity33",
		"BoryscoAndeiy",
		"borysko_an71847",
		"borysko_mykyta",
		"Borysko_vasiko",
		"Boryslavvv",
		"BoryzY88443",
		"boyka_shev",
		"boyko_kovi",
		"BoykoMykol94110",
		"Bradoski_5",
		"BravermanArc4",
		"BrownLizbeth_",
		"buchko_cherkas",
		"Budanov_1",
		"BurguessJ",
		"BurianAndriy",
		"Burianfranko",
		"BuruckA121",
		"Buzz2694388111",
		"car48173",
		"Carlos246vb",
		"CarlosMill741",
		"carolann1_",
		"catia230t",
		"catsanct",
		"CDacel53122",
		"CharloPedia",
		"Chenwei9657",
		"ChernenkoAlek",
		"choban_oleksiy",
		"Chobotenko01",
		"CjShevchuk",
		"Claramykhalia",
		"Confidiencegirl",
		"Contact_Robb",
		"d_mudryk",
		"d_yevheniy70802",
		"Dahmedjaafar",
		"Dan_Lyaksandro",
		"Daniel211442628",
		"daniela_kalyna",
		"DaniellaDa76774",
		"DanielNGCrew",
		"Danielscot53929",
		"Danilourain232",
		"DannyDanylo",
		"danshevchenko11",
		"DanyDmitro",
		"danylo_mat43592",
		"danylo_mat8412",
		"Danylo246",
		"Danylo275350580",
		"DanyloAndri",
		"danyloAndriy11",
		"DanyloBondarenk",
		"DanyloGrygoriy",
		"danyloivan5668",
		"DanyloKrys858",
		"danylomykhailo",
		"Danyoleksandr",
		"Daryna_olena1",
		"DaveAnders85976",
		"davidabrovich",
		"DavidHildeb122",
		"davidtaras8",
		"DavisDougl26737",
		"Davyd3421",
		"DavydLeoni72262",
		"DavydPanas29381",
		"DemianMarlo",
		"Denhansen",
		"denys_marko",
		"Denysbohuslav22",
		"DenysKoval23",
		"Denystaras",
		"Denysyaros300",
		"dexman982260",
		"DimaDzek",
		"Dimitro2233",
		"DMikhalo73458",
		"dmitri_igo58118",
		"Dmitriy_Mikhail",
		"Dmy_Volodymyr",
		"dmytro_anastass",
		"Dmytro1122",
		"DmytroBohd86385",
		"dmytrokovalmart",
		"DmytroOlek59244",
		"DmytroTodorov",
		"dmytruk_marko",
		"DmytryFedorenko",
		"dnytrokotsiuba",
		"Dobryak39340867",
		"DogDayz17",
		"dogshelt",
		"DonaldStew76777",
		"Dorexxy15",
		"Dovxhen",
		"Dovzhenko02",
		"Dr_Bilalp",
		"draisha43",
		"Dream_Haund",
		"Drkgl141",
		"DymtrusDrach",
		"EchoMyklola",
		"EchoSnsd",
		"Egorova__olia",
		"Eira534261Eira",
		"Eswar21123210",
		"EthanTsiklauri",
		"evhenavlovykova",
		"EwurumGood5357",
		"FaddeiIvan",
		"faddeiivan444",
		"falconua1",
		"Far_do19",
		"faradaysboy",
		"farhadaltun",
		"fedir__mykola",
		"fedir_derkach",
		"fedir_mykhailo",
		"Fedir_Yaroslav",
		"fedir4167",
		"Fedir46",
		"FedirArtem81062",
		"FedirBohdan",
		"FedirBorys39105",
		"fedire24972",
		"FedirKravchenko",
		"FedirMykhailo1",
		"fedirokasana",
		"FedirShevchenko",
		"fedirvolodymyr1",
		"Feericoo",
		"ffzq20",
		"FKrychevsk39331",
		"FLianneo",
		"FLysenko69058",
		"forukraine3312",
		"forwardmatch5",
		"Franclszekmazur",
		"Frank_mull2",
		"FrankoLyashenko",
		"frankolysenko",
		"FRD0680680",
		"FREE_UKRAINE199",
		"freekz_game",
		"G_brittany_",
		"Gabriel23689",
		"Ganesh17216987",
		"Garkavenko001",
		"Garyaliduman",
		"GeorgeDamian0",
		"Georgepetrenko9",
		"GeorgeZaika19",
		"GerarsxCrane",
		"Ghostofavdiivka",
		"giorgig3141811l",
		"GIUSEPPE_MTN",
		"GlibWAR",
		"gorBondare65176",
		"GrahamScott_71",
		"GreatPapi1",
		"GregiVyacheslav",
		"Grigoryivan",
		"grozovsky_ivan_",
		"GrygoriyTrubch1",
		"GustosV",
		"Guzneranton",
		"HadeonAnton16",
		"halyna_1",
		"hamada566610",
		"hamza4245",
		"hanna_mom98",
		"HannaSemen5",
		"Harri_Ecit",
		"Harri_No_Est",
		"Harri23ggt3",
		"help_dogs_need",
		"Henry_Danylo",
		"HenryPhili42165",
		"HenryWashi1196",
		"hhfaisal_",
		"hryhorchuk_a",
		"hryhorchuk_p",
		"hryhoriymatviy",
		"Hryshchenko01",
		"Iamlale1",
		"ICohen82999",
		"IdcabasaJr",
		"IgoMorozov5733",
		"IgorIvan",
		"igormykola88",
		"IkemefunaE20275",
		"Ilay_kyva",
		"Iqbal_kesuma27",
		"Iryna_240",
		"isaiatem",
		"israelhelman",
		"ivan__ivan3456",
		"Ivan__Kova",
		"Ivan_Fella",
		"ivan_justjust",
		"ivan_mykola",
		"ivan_tsy62",
		"ivan13rt",
		"Ivan58255138",
		"IvanAndriy34779",
		"ivanbohdan333",
		"ivanbohdan3332",
		"ivanbondar625",
		"ivanboul",
		"ivanboyan09",
		"IvanHrozovakii",
		"IvanKoval31782",
		"ivankrystiyan48",
		"IvanMykhaylo",
		"ivanna_olha",
		"Ivanna5900",
		"ivannameln6180",
		"IvannaShev8589",
		"ivanoleks_o",
		"ivanon787",
		"IvanovVeronika3",
		"Ivanpet3456",
		"Ivanpetro436",
		"IvanPolishchu",
		"ivanto457897",
		"IvanYusty10",
		"iwonttextU",
		"JackieAscroft",
		"Jackson84458745",
		"JamesWilli28992",
		"JamesYe11614188",
		"jeffrey_451",
		"Jennistachura",
		"jennysimeonne",
		"Jewel_Onyedolar",
		"JimmyFrank4476",
		"jimmyFrank85013",
		"jimuel_pogi10",
		"jmvasquez1974__",
		"jmVasquezz_1974",
		"Jobloski23",
		"john404m",
		"JohnHeimke",
		"johnUS1112",
		"Joseph11610047",
		"JoshuaB32386334",
		"juliane1102",
		"kaNkak01",
		"KarenRiccios",
		"karynaKukhar",
		"kaspa6767",
		"KatarynaBekar",
		"KaterinaKo73380",
		"Kateryna_012",
		"kateryna24702",
		"kateryna74190",
		"KatryaD",
		"kaviwat",
		"kelviin_igorr",
		"Kenny_lanezz",
		"kevintherig",
		"Kharkiv_Animals",
		"Kharkiv_Shelter",
		"KhersonAnimals",
		"Khrysty91",
		"Khrystyna_boris",
		"kingandriy_",
		"kira_choas",
		"kira_inna01",
		"kira_olenaukr",
		"KiryavainenIlly",
		"kochevenk",
		"Kolisnyk11A",
		"KonoplyovAndrii",
		"KostiantynGlib",
		"KostinantynKy",
		"Kostyan1960",
		"kostyanko38009",
		"KostyantynAlek",
		"Kostyantynandri",
		"KostyantynMarko",
		"kovalcharles001",
		"kovalenko_Tyson",
		"kovalenko01serh",
		"KovalenkoF4915",
		"KravchenkoDan2",
		"KrotevychB",
		"krystDAnylo",
		"Krystiyan333",
		"Krystiyan8689",
		"KrystiyanO8947",
		"KrystiyanPopov",
		"krystiyanYakiv4",
		"KryvonisTa64152",
		"KunitsynOleksiy",
		"kurt_armstrong1",
		"KwinMarko",
		"kyianyn204",
		"kyrylo_01",
		"Kyryloanton",
		"KyryloDmytro",
		"kyrylovladyslav",
		"Lambo_raul001",
		"LaRostyslav",
		"larrytex15262",
		"LaurisPetr93934",
		"LaursenKahuna",
		"LeeWindsor_",
		"lelechko_o",
		"lendingwithmeg",
		"Leonidas_cy01",
		"LeonidJohn212",
		"LeonidSymon1",
		"LeonidZ77301",
		"leow33799",
		"letisya2508",
		"liborovska",
		"lillynatalya001",
		"lobinerugocaja",
		"Lonnie_Conno",
		"Loveforanimal05",
		"LTJG_mariyaolek",
		"LubomirY12",
		"lvivanimalshelt",
		"lyaks22",
		"lyaksandro_Dany",
		"lyaksandro_s",
		"Lyaksandro2",
		"Lyaksandrosymo",
		"lykasandro81813",
		"MadyarmarkCo",
		"makcumyc_88",
		"MaksymFf",
		"MalaJulia346",
		"Marchenko_RA",
		"marcojosh08",
		"mariaderus11067",
		"MarianThom87070",
		"Mariaveronika21",
		"Marica_ehly",
		"mariya235678",
		"MariyaAndriy01",
		"MariyaKozak3",
		"markartyom",
		"markiv_vitalii",
		"MarkivVitalii",
		"Marko_Fedir",
		"marko_olek89419",
		"Marko_pavlo2",
		"Marko098fedir",
		"Marko0Pankevych",
		"marko2mar",
		"MarkoA824853",
		"MarkoBoyan",
		"markofedir",
		"MarkoKondratyuk",
		"markol590",
		"MarkoTymofij",
		"markusv32",
		"markv0001",
		"Markytipp",
		"MartaDemy",
		"martaDemyanchu",
		"martentrokymyro",
		"Masha3erMody",
		"mashael2820",
		"Matteo0b7",
		"Mattthomp8",
		"Matviy_F_Osip",
		"Matviy052",
		"MatviyC",
		"MatviyDany43543",
		"matviydany69075",
		"MatviyDanylo332",
		"MaximTommy2",
		"MBuble6692",
		"mercythecat01",
		"MerrickGar9613",
		"mertnii45105",
		"mertnii7289",
		"mhelembemd",
		"MiaMalk02024468",
		"michealJrp",
		"MikeSte98944360",
		"miller_msi",
		"Mitin_Oleksandr",
		"MMatviyko",
		"mmpadettan",
		"MNA486",
		"ModMykola11133",
		"Molfar4437031",
		"mr_ezi",
		"Mr_NesterenkoY",
		"Mr_vlad_dmitry",
		"mudryk_mykhailo",
		"MVelerii24872",
		"MVelerii61316",
		"MVelerii74923",
		"mykalo13",
		"Mykhail_1",
		"Mykhailo_vol01",
		"Mykhailo0012",
		"Mykhailo90",
		"mykhaolek",
		"MykhayloOleksiy",
		"mykola_5",
		"mykola_andriy01",
		"Mykola_borysko",
		"mykola_kolisny0",
		"mykola132",
		"MykolaD411",
		"MykolaDamain",
		"MykolaDanylo",
		"MykolAleksander",
		"Mykolaokeksiy",
		"MykolaOleskij",
		"MykolaOstp",
		"MykolaS20625",
		"MykolaS5152",
		"mykyta_38",
		"Mykyta_kry",
		"Mykyta_Taras02",
		"mykyta000",
		"NastunyeR",
		"Nataliya_Ga",
		"Nataliya332",
		"Nataliya591",
		"NataliyaAterm",
		"Naturepure24",
		"Nazar_Oleksiy",
		"NazarBohda",
		"Nishith62190342",
		"NJCJ875",
		"Novikoh11",
		"novinsky_ole",
		"Nurirahmadiany1",
		"nurteagituch",
		"NYana___123",
		"NYURA177737",
		"O_Potiomkin",
		"Ocalebigorr",
		"odesabohdan",
		"Odessa_Sheltero",
		"Odessa_strays84",
		"OdessaShelter",
		"oksana27653",
		"OKunitsyn14581",
		"ol3ks1y",
		"OlegFedir",
		"olegigor22",
		"OlegIgor334",
		"OlehPedro",
		"OlekPetrol31168",
		"oleksanarcus",
		"Oleksander822",
		"oleksanderandri",
		"Oleksanderdenys",
		"Oleksandr143",
		"Oleksandra1222",
		"Oleksandra2221",
		"oleksandrandry",
		"OleksiiChubash",
		"oleksiy_bohdan",
		"Oleksiykoval19",
		"OleksiyPetro",
		"OleksiySokolov",
		"OlekzandrP",
		"olelsky_danylo",
		"Olena_Als",
		"olena_zelenska",
		"Olenanikolay",
		"Olenapetrova352",
		"Olexi_slavy",
		"Olgamudryk5",
		"OliviaAntoni436",
		"OlPavlo",
		"Olsen_chenko",
		"Olyagorova",
		"OnatiNax",
		"OPomaxa",
		"orest_rusl83920",
		"OrestRuslan",
		"ORYNKO_",
		"Osamavi72279163",
		"ostaltsev_Alex",
		"ostap_volo17945",
		"OttovikSimmer",
		"p_andriy2",
		"PadreRovnuy",
		"Palvo10Li",
		"PanchenkoFedir",
		"pankration_648",
		"paramedic_koval",
		"Parkerkenz0633",
		"Patrycia_west",
		"pavlo_anichka",
		"pavlo_kazarin",
		"pavlo_marko4",
		"Pavlo0015",
		"pavloandij0001",
		"pavloborysko7",
		"PavloStepanow",
		"peremoha_myr",
		"petrenko_andri",
		"PetrenkoSergio_",
		"petro_andrij",
		"Petro4903",
		"PetroFedir3638",
		"petromykhailo",
		"petrookhotin112",
		"petrovychakhtem",
		"PetrovychS16375",
		"Petrussopopvych",
		"PetsReacue",
		"PhilemonIzibed1",
		"PKryvonis81160",
		"PolinaAleksand_",
		"popov9900",
		"pramioo7",
		"prayforukr0111",
		"prayforukr10",
		"Proudprius6",
		"RandyAndreeva",
		"reason2223",
		"remaVolodymy",
		"rescuehomea",
		"robertkoval",
		"Roman88189",
		"RomanovOleksan",
		"rose_keti",
		"Rost5889Matviy",
		"Rostyslav896",
		"RostyslavIvan",
		"ryann_lowe7",
		"rybakova_i7380",
		"SaveForUA4577",
		"sergeant_miro",
		"Sergeivinstev",
		"SerhiyShaptala_",
		"SerhiyShaptalau",
		"severynsin9256",
		"SeyithanKarakas",
		"shaw_briggs0",
		"Shellhamer56969",
		"Shevchenko_alez",
		"shimin_shima",
		"Shira799",
		"ShukriPetrenko",
		"shuliakoo1",
		"Sign_My_Rocket",
		"Simadhot",
		"SKalfman3111",
		"slava_vasyl",
		"Smilimov",
		"Smirnoff_Yakov3",
		"smithwright811",
		"SmyrnovVik67329",
		"Snezanvolodymyr",
		"Snibohd",
		"SofiyaAnna090",
		"sohpiedee1",
		"SommerAnnika",
		"somsak_arthit",
		"sonreiiiir",
		"SophiaM84045860",
		"stabi_k",
		"stanleystyles5",
		"SteveCo67922864",
		"SteveMi09873966",
		"StewardPet33471",
		"StolyaruA",
		"Stuartradcliff",
		"Svyatoslavpanas",
		"swiftsholy",
		"SyBoyko",
		"symo86973",
		"Symon_Brown59",
		"symon_oleksiy81",
		"SymonYaroslav",
		"symonyaroslav21",
		"SZbroynyy65484",
		"Tammy_1470",
		"Tania_Goro",
		"Tapac_dmitro",
		"TapahKpyk973",
		"taras_deiak",
		"taras_ivan35005",
		"Taras10A",
		"Tarasanton12",
		"tarasbo08",
		"TarasDanyl",
		"tarasdanylo05",
		"TarasGeorgy",
		"TarasIvan067",
		"TarasOfficial",
		"TarasPetro0",
		"Teigenhassan1",
		"TerekhovEv35335",
		"Tereshchenkosly",
		"The__Man99",
		"TheFlight927",
		"thomanthony_",
		"ThomasWalter__",
		"timo_andriy",
		"TkachenkoRagnar",
		"Tolya_wind",
		"TomlinsonF61220",
		"TsarenkoGan001",
		"turbo87231",
		"UAanimalres",
		"UGOERIk",
		"ujnkiev",
		"ukraine_slava1",
		"UkraineArmy21",
		"UkraineDFS",
		"Ukrainedogscar2",
		"ukrainefight25",
		"Ukrainefighter1",
		"UkraineForce_",
		"ukraineforce012",
		"ukraineforlife0",
		"UkraineRescueH1",
		"UkraineSF1",
		"Ukrainianarmy8",
		"ukrainiansquad",
		"ukriaine123",
		"ULisenka73993",
		"UOhrim",
		"uzomaj769",
		"v_vivcharenko",
		"valerii_marku",
		"vanya_kiev",
		"Vasylborys7",
		"VasylIlona",
		"Vasylsmokke",
		"VDM__001",
		"VeleriiMark",
		"VicSpnz",
		"viktor_pa2",
		"vitalii_markiv",
		"vitaliimarkiv",
		"vladank9",
		"vladimir_shev55",
		"Vladislav1889",
		"VNoharna",
		"voiaed78137",
		"voicetostrays",
		"VolodIvasy",
		"volodymr09",
		"volodymy0",
		"Volodymy5",
		"volodymyr_001",
		"volodymyrb48819",
		"VolodymyrGroys3",
		"Volodymyrky",
		"VolodymyrR12",
		"VolodymyrYakiv",
		"volomykola",
		"Volovan090",
		"VStalkersx",
		"WalterOtto30496",
		"WalterOtto69314",
		"warrencrawford_",
		"wendyshelter1",
		"whizzpel",
		"William04117192",
		"WOLODYMYR0",
		"Xbadcharacter",
		"XFunny4u",
		"Yakiv_2",
		"Yakiv_dima",
		"yakiv_kyn",
		"Yakiv111111",
		"Yakivv2",
		"YanaKryvonis1",
		"Yaroslav_artem_",
		"Yaroslavkra",
		"YarynaDmyt72377",
		"Yatseny01",
		"yevhen_cohen1",
		"yevhencohen_",
		"YEVHENIYIGOR",
		"YFaddei",
		"YinksFx",
		"young_nicole33",
		"Yurii48y",
		"YuriRosty1031",
		"yustyk_avgustin",
		"zichenko_a",
		"Zin_Olena84",
		"ZorianShkrika",
		"ZsuPetrooo",
		"Asio_fella_nafo",
		"carmiepmiep3432",
		"nafer2162215221",
		"ukraininsquad",
		"UkrainianS33627",
		"trianziu",
		"AriahBen2O24",
		"russiamustlose",
		"depronatorr",
		"seppo_sana",
		"theIiamnissan",
		"TraiascaRomania",
		"Yanazavod",
		"gaz__EOD",
		"theghostofkiev0",
		"giorgig33418111",
		"antinafo3",
		"DekanadzeM5627",
		"SegulahSurprise",
		"1ANDREWMERCADO",
		"USAmbMOD",
		"USAmbModerate",
		"USAmbNAFO",
		"nafobot69",
		"BomberFella",
		"dietdanish",
		"TheCoffeeEater",
		"mykolapastux",
		"Nafofellagoat",
		"YellowUkraine",
		"uafsans",
		"mbanda15",
		"ellie_nora17"




	]




main()

