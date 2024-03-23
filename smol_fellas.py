import importlib, base64, functools, pickle
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
PASSWORD = "!"



smol_limit = 500		# Fellas with more than this amount of followers are not considered smol 

def main():
	global USER_NAME, PASSWORD, TARGET_USER

	fella_dict = loadFellas()
	print_stats(fella_dict)



	if len(sys.argv) > 2:
		USER_NAME = sys.argv[1]
		PASSWORD = sys.argv[2]

	if not USER_NAME or not PASSWORD:
		print("You must supply a username and password to log in to xhitter")
		print("Syntax: py smol_fellas.py username password")
		quit()



	print("\n\n\n****** LET'S GO FIND SOME SMOL FELLAS! ******")
	print("\nUsername: " + USER_NAME)
	print("Password: ********")
	
	login(USER_NAME, PASSWORD)

	run(fella_dict)

def run(fella_dict):
	
	while True:

		# Run a session
		print("\n\nSESSION")
		session(fella_dict)
		print_stats(fella_dict)
		driver_get("https://twitter.com/" + USER_NAME)


		if datetime.datetime.now().hour > 6:
			if random.random() < 0.33 or datetime.datetime.now().isoweekday() == 5:
				post_message(output_string(fella_dict))
			sleep_rand(60*45, True)
		else:	
			post_message(output_string(fella_dict))
			print("It's time for bed.")
			time.sleep(60*60*8)
	
def session(fella_dict):

	# List all the unscraped fellas
	scrape_list = []
	for fella in fella_dict:
		if fella_dict[fella]['scraped'] == False and not fella_dict[fella]['ignore']:
			scrape_list.append(fella)

	print ("There are " + str(len(scrape_list)) + " fellas to be scraped")
	scrape_index = 0

	# Things we can do in a session
	actions = [
		visit_fella,
		scrape_fella,
		scrape_fella
	]

	# We'll do various things this session
	for i in range(1, random.randint(10,30)):
		print("\n" + str(i) + ": ", end="")
		scrape_index += random.choice(actions)(fella_dict, scrape_list[scrape_index])
		sleep_rand(10)



def scrape_fella(fella_dict, fella):
	print("Scrape @" + fella)
	body_text = driver_get("https://twitter.com/" + fella + "/followers")
	insertStyle()

	if "These posts are protected" in body_text or "Account suspended" in body_text or "Something went wrong. Try reloading" in body_text:
		print("Account protected or suspended.")
		fella_dict[fella]['scraped'] = datetime.datetime.now()
		return 1


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
				saveFellas(fella_dict)
				fella_dict[fella]['scraped'] = datetime.datetime.now()
				return 1

			index += 1
			if index % 200 == 0:
				saveFellas(fella_dict)

			link = follower.find_element(By.CSS_SELECTOR, "a")
			user = link.get_attribute('href').replace("https://twitter.com/", "")
			if user in done_list:
				continue


			try:
				driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center', inline: 'nearest'})", follower)
				time.sleep(0.5)			
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


				if ("nafo" in txt or "fella" in txt or "fellina" in txt or "bonk" in txt) and (user not in block_list()):

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
						fella_dict[user] = {
							"following_count": following_count,
							"follower_count": follower_count,
							"found": datetime.datetime.now(),
							"checked": datetime.datetime.now(),
							"vetted": False,
							"scraped": False,
							"tweeted": False,
							"ignore": False
						}
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
				print(e)
				time.sleep(10)
			done_list.append(user)


def visit_fella(fella_dict, fella = None):


	smol_fella_dict = get_smol_fellas(fella_dict)
	fella = random.choice(list(smol_fella_dict.keys()))

	print("Visiting @" + fella)
	driver_get("https://twitter.com/" + fella)
	time.sleep(3)
	check_fella(fella, smol_fella_dict)

	if not smol_fella_dict[fella]['ignore']:
		tweets = driver.find_elements(By.CSS_SELECTOR, "article[data-testid='tweet']")
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
		time.sleep(1)

		if random.random() > 0.5 and like_btn:
			print("Like")
			like_btn.click()
			time.sleep(1)

		if random.random() > 0.5 and rt_btn:
			print("Retweet")
			rt_btn.click()
			time.sleep(1)
			driver.find_element(By.CSS_SELECTOR, "div[data-testid='Dropdown'] div[data-testid='retweetConfirm']").click()
			sleep_rand(3)

	return 0

def check_fella(fella, smol_fella_dict):
	print("Check @" + fella)
	body_text = driver.find_element(By.CSS_SELECTOR, "body").text
	tweets = driver.find_elements(By.CSS_SELECTOR, "article[data-testid='tweet']")
	if "Account suspended" in body_text or "This account doesn’t exist" in body_text or len(tweets) == 0:
		smol_fella_dict[fella]['ignore'] = True 
	else:
		followers_link = get_link_containing("/verified_followers")
		follower_count = int(followers_link.find_element(By.CSS_SELECTOR, "span:first-child > span").text.replace("K", "000").replace(".", "").replace(",", ""))

		following_link = get_link_containing("/following")
		following_count = int(following_link.find_element(By.CSS_SELECTOR, "span:first-child > span").text.replace("K", "000").replace(".", "").replace(",", ""))

		smol_fella_dict[fella]["following_count"] = following_count
		smol_fella_dict[fella]["follower_count"] = follower_count

	smol_fella_dict[fella]["checked"] = datetime.datetime.now()






def post_message(content):
	time.sleep(5)
	driver.find_element(By.CSS_SELECTOR, "a[data-testid='SideNav_NewTweet_Button']").click()
	time.sleep(3)
	driver.find_element(By.CSS_SELECTOR, "div[aria-modal='true'] br[data-text='true']").send_keys(content) 
	time.sleep(3)
	tweet_btn = driver.find_element(By.CSS_SELECTOR, "div[aria-modal='true'] div[data-testid='tweetButton']")
	driver.execute_script("arguments[0].click()", tweet_btn)
	print("\n\n---Tweet Sent at " + datetime.datetime.now().strftime("%H:%M") + "---")
	print(content)
	print("---------------------------- \n")
	time.sleep(5)



def sleep_rand(t, log=False):
	r = random.random() - 0.5
	if log:
		print(f"Pausing for " + str(datetime.timedelta(seconds=int(t+t*r))), flush=True)
		print(f"Resuming at " + (datetime.timedelta(seconds=int(t+t*r)) + datetime.datetime.now()).strftime("%H:%M:%S"), flush=True)
	time.sleep( t+t*r )


def login(username, password):
	sleep_rand(1)
	driver_get("https://twitter.com/i/flow/login")
	sleep_rand(8)
	driver.find_element(By.CSS_SELECTOR, "input").send_keys(username)
	sleep_rand(2)
	driver.find_element(By.CSS_SELECTOR, "div[data-viewportview='true'] > div > div > div:nth-child(6)").click()
	time.sleep(8)
	driver.find_element(By.CSS_SELECTOR, "input[name='password']").send_keys(password)
	sleep_rand(2)
	driver.find_element(By.CSS_SELECTOR, "div[data-testid='LoginForm_Login_Button']").click()
	time.sleep(5)


def output_string(fella_dict):

	tweet_fella_dict = {}
	smol_fella_dict = get_smol_fellas(fella_dict)
	for fella in smol_fella_dict:
		if smol_fella_dict[fella]['tweeted'] and (datetime.datetime.now() - smol_fella_dict[fella]['tweeted']).days > 7:
			tweet_fella_dict[fella] = smol_fella_dict[fella]



	str1 = ["Got some more smol fellas for you", "Here are some little fellas", "These are smol fellas", "Here's some lesser-known fellas"]
	s1 = random.choice(str1)
	str2 = [" with not many followers of their own. ", " who need a bit of NAFO love. ", " who need your follows. ", " so you can follow and boost. "]
	s2 = random.choice(str2)
	str3 = ["Go give them a boost!", "To follow is the way.", "See a fella, follow a fella!"]
	s3 = random.choice(str3)
	ostr = s1 + s2 + s3 + "\n\n"

	str4 = ["*This list is unvetted.", "*Do your own due diligence please", "*Always double-check accounts before following", "*NAFO authenticity not guaranteed"]
	s4 = '\n' + random.choice(str4)
	s5 = "\n\n#nafo #smolfellas"

	while True:
		fella = random.choice(list(smol_fella_dict.keys()))
		fella_str = "@" + fella + " - " + str(smol_fella_dict[fella]['follower_count']) + "\n"
		if len(ostr + fella_str + s4 + s5) < 280:
			if fella_str not in ostr:
				ostr += fella_str
				fella_dict[fella]['tweeted'] = datetime.datetime.now()
		else: 
			break
	ostr += s4 + s5
	return ostr




def loadFellas():

	if os.path.exists("fellas.pkl"):
		with open('fellas.pkl', 'rb') as f:
			fella_dict = pickle.load(f)
			clean_list(fella_dict)
	else:
		fella_dict = {}
	validate_fellas(fella_dict)
	return fella_dict

def saveFellas(fella_dict):
	clean_list(fella_dict)
	with open('fellas.pkl', 'wb') as f:
		pickle.dump(fella_dict, f)
	with open('fellas.pkl.bak', 'wb') as f:
		pickle.dump(fella_dict, f)
	print("Saved " + str(len(fella_dict)) + " fellas")

def validate_fellas(fella_dict):
	for fella in fella_dict:
		if not "following_count" in fella_dict[fella]:
			fella_dict[fella]["following_count"] = 0
		if not "following_count" in fella_dict[fella]:
			fella_dict[fella]["follower_count"] = 0
		if not "found" in fella_dict[fella]: 
			fella_dict[fella]["found"] = datetime.datetime.now()
		if not "checked" in fella_dict[fella]: 
			fella_dict[fella]["checked"] = False
		if not "vetted" in fella_dict[fella]: 
			fella_dict[fella]["vetted"] = False
		if not "scraped" in fella_dict[fella]: 
			fella_dict[fella]["scraped"] = False
		if not "tweeted" in fella_dict[fella]: 
			fella_dict[fella]["tweeted"] = False
		if not "ignore" in fella_dict[fella]: 
			fella_dict[fella]["ignore"] = False
		fella_dict[fella]["following_count"] = int(fella_dict[fella]["following_count"])
		fella_dict[fella]["follower_count"] = int(fella_dict[fella]["follower_count"])
		if fella in block_list():
			fella_dict[fella]["ignore"] = True
		for term in block_patterns():
			if term in fella:
				fella_dict[fella]["ignore"] = True

	print ("Validated fella data")


def insertStyle():

	styleScript = """
	let styleEl = document.createElement("style")
	styleEl.innerHTML = "div[data-testid='cellInnerDiv']{border-left: solid 5px white} div[scraped='true']{border-left: solid 5px #bbb} div[scraped='true'][fellatype='smol']{border-left: solid 5px #ffd700} div[scraped='true'][fellatype='large']{border-left: solid 5px #0057b8}"
	document.body.prepend(styleEl)
	"""

	driver.execute_script(styleScript)

def print_stats(fella_dict):
	smol_count = 0
	big_count = 0
	scraped_count = 0
	ignore_count = 0
	for fella in fella_dict:
		if fella_dict[fella]['scraped'] != False:
			scraped_count += 1
		if fella_dict[fella]['follower_count'] < smol_limit:
			smol_count += 1
		if fella_dict[fella]['follower_count'] >= smol_limit:
			big_count += 1
		if fella_dict[fella]['ignore']:
			ignore_count += 1
	print("Fellas:      " + str(len(fella_dict)))
	print("Big fellas:  " + str(big_count))
	print("Smol fellas: " + str(smol_count))
	print("Scraped:     " + str(scraped_count))
	print("Ignoring:    " + str(ignore_count))

def clean_list(fella_dict):

	for b in block_list():
		if b in fella_dict:
			del fella_dict[b]
	return fella_dict

	for b in block_patterns():
		for f in fella_dict:
			if b.lower() in fella.lower():
				del fella_dict[f]

def driver_get(url):

	driver.get(url)
	time.sleep(3)
	body_text = driver.find_element(By.CSS_SELECTOR, "body").text
	if "Your account has been locked" in body_text:
		print("They're on to us!  Time for an Arkose.  Press Enter when account unlocked.")
		input()

	try:
		driver.find_element(By.CSS_SELECTOR, "div[data-testid='BottomBar'] div[role='button']:first-child").click()	
		sleep_rand(5)
	except:
		pass

	return body_text

def get_smol_fellas(fella_dict):
	smol_fella_dict = {}
	for fella in fella_dict:
		if fella_dict[fella]['follower_count'] < smol_limit:
			smol_fella_dict[fella] = fella_dict[fella]
	return smol_fella_dict

def get_link_containing(url_fragment):
	for el in driver.find_elements(By.CSS_SELECTOR, "a"):
		if url_fragment in el.get_attribute("href"):
			return el



def block_patterns():
	return [
		"TimDobson"
	]


def block_list():
	return [
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
		"nafer2162215221"

	]




main()

