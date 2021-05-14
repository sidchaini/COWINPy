import requests
import json
import smtplib, ssl
from email.message import EmailMessage
import os
from datetime import datetime
from dateutil.tz import gettz
import time
import getpass
import base64
import warnings

def create_preferences(pref_file):
	if os.path.isfile(pref_file):
		os.remove(pref_file)
	print("Creating a new preferences file. Please enter the following details:")
	
	pref_dict = {}
	pref_dict["name"] = input("Enter your name: ")
	pref_dict["age"] = int(input("Enter your age: "))
	pref_dict["receiver_email"] = input("Enter email id to which email will be sent: ")
	pref_dict["pin"] = int(input("Enter your pincode: "))

	vac_input = input('Enter vaccine type. It should be either of\n\t1. "COVISHIELD"\n\t2. "COVAXIN"\n\t3. "ANY": ').upper()
	if vac_input == 1 or vac_input == "COVISHIELD":
		pref_dict["required_vaccine_type"] = "COVISHIELD"
	elif vac_input == 2 or vac_input == "COVAXIN":
		pref_dict["required_vaccine_type"] = "COVAXIN"
	else:
		pref_dict["required_vaccine_type"] = "ANY"

	# ADD DISTRICT SEARCH LATER
	# searchby_input = input('Do you want to search by PIN or DISTRICT?. It should be either of\n\t1. "PIN"\n\t2."DISTRICT"').upper()
	# if searchby_input == 1 or searchby_input == "PIN":
	# 	pref_dict["search_by"] = "PIN"
	# else:
	# 	pref_dict["search_by"] = "DISTRICT"
	
	pref_dict["bot_version"] = 1.0
	pref_dict["sleep_refresh"] = 10
	pref_dict["sleep_success"] = 3600

	print(f"A few advanced settings were setup automatically. Advanced users wanting to change this are encouraged to manually edit {os.path.join(os.getcwd(),pref_file)} and restart the program.")

	with open(pref_file, "w") as fp:
		json.dump(pref_dict, fp, indent=4)
	
	send_email(pref_dict["receiver_email"],get_email_start_text(pref_dict["name"]),subject="Welcome to COWINPy!")
	
	return pref_dict


def start_up(pref_file=".preferences.txt"):
	if os.path.isfile(pref_file):
		print(f"Welcome back! Your previous settings have been found. What would you like to do?")
		print("\t1. Resume previous run, with the exact settings.")
		print("\t2. Start afresh.")
		choice = int(input("Enter 1 or 2"))
		if choice==1:
			with open(pref_file,"r") as fp:
				pref_dict = fp.read()
				pref_dict = json.loads(pref_dict)
		elif choice==2:
			pref_dict = create_preferences(pref_file)

	else:
		choice = 2
		print(f"Welcome to COWINPy! A preferences file was not found. So, a new one will be created in {os.path.join(os.getcwd(),pref_file)}.")
		pref_dict = create_preferences(pref_file)

	name = pref_dict["name"]
	age = pref_dict["age"]
	receiver_email = pref_dict["receiver_email"]
	pin = pref_dict["pin"]

	required_vaccine_type = pref_dict["required_vaccine_type"]

	bot_version  = pref_dict["bot_version"]
	sleep_refresh = pref_dict["sleep_refresh"]
	sleep_success = pref_dict["sleep_success"]

	return name, age, receiver_email, pin, required_vaccine_type, bot_version, sleep_refresh,sleep_success, choice

# ADD DISTRICT LATER
# def get_cowin_district(state_name,district_name):


def send_email(receiver_email,message, subject=f"COWINPy Update - {datetime.now(tz=gettz('Asia/Kolkata'))} IST"):
	port = 465  # For SSL
	smtp_server = "smtp.gmail.com"
	sender_email = "cowinpython@gmail.com"  # Enter your address
	msg = EmailMessage()
	msg.set_content(message)
	msg['Subject'] = subject
	msg['From'] = sender_email
	msg['To'] = receiver_email
	context = ssl.create_default_context()
	with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
		server.login(sender_email, base64.b64decode("QXNkMTIzYXNkQA==").decode("utf-8"))
		server.send_message(msg)

def get_email_update_text(name, availablels, datels, agels, typevacls, centernamels,feels):
	message =f'''Dear {name},
There are {availablels} TOTAL slots you can book right now for {datels}, age limit = {agels}!
Book soon!

Available capacity:\t{availablels}
Age:\t{agels} and above.
Date:\t{datels}
Vaccine:\t{typevacls}
Center:\t{centernamels}
Fee Type:\t{feels}.

Please check https://www.cowin.gov.in/home for more details!

Regards,
Team COWINPy
'''
	return message

def get_email_start_text(name):
	message = f'''Dear {name},
Thank you for registering with COWINPy. This is an example email. You will get an email like this if any slots are available.
Please note that a maximum of 1 email will be sent every hour to prevent spam.

Regards,
Team COWINPy'''
	return message

def get_cowin_dict_by_pin_by_api(pin,today=datetime.now(tz=gettz('Asia/Kolkata')).date().strftime("%d-%m-%Y")):
	protected_url = f"https://cdn-api.co-vin.in/api/v2/appointment/sessions/calendarByPin?pincode={pin}&date={today}"
	protected_url_alt = f"https://api.cowin.gov.in/api/v2/appointment/sessions/calendarByPin?pincode={pin}&date={today}"
	public_url = f"https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByPin?pincode={pin}&date={today}"
	public_url_alt = f"https://api.cowin.gov.in/api/v2/appointment/sessions/public/calendarByPin?pincode={pin}&date={today}"

	urls = [protected_url,protected_url_alt,public_url,public_url_alt]
	blockedcounter = 0
	for i in range(8):
		url = urls[i%4]
		r = requests.get(url)
		if r.ok:
			break
		if not r.ok and ("blocked" in r.text or "Forbidden" in r.text):
			blockedcounter += 1
	if blockedcounter>2:
			raise RuntimeError("API Request blocked. Consider switching to bot_version 2.0 instead, which is selenium based.") 
	if i == 0 or i == 1:
		pubpro = "Protected"
	else:
		pubpro = "Public"
		warnings.warn('Public API is being used. Consider switching to bot_version 2.0 instead, which is selenium based for faster updates.')

	cowin_dict = json.loads(r.text)
	return cowin_dict

def prepare_driver():
	from seleniumwire import webdriver
	from selenium.webdriver import ActionChains
	from selenium.webdriver.common.keys import Keys
	from selenium.webdriver.support.select import Select
	from webdriver_manager.chrome import ChromeDriverManager
	# Look into headless later
	# from selenium.webdriver.chrome.options import Options
	# chrome_options = Options()
	# chrome_options.add_argument("--headless")
	global driver
	# driver = webdriver.Chrome(ChromeDriverManager().install(),chrome_options=chrome_options)
	driver = webdriver.Chrome(ChromeDriverManager().install())
	driver.maximize_window()
	driver.implicitly_wait(5)
	# print("Chrome driver has been created.")

	while True:
		flag=1
		try:
			driver.get("https://selfregistration.cowin.gov.in/")
			time.sleep(1)
			driver.find_elements_by_class_name("mat-input-element")[0].send_keys("7021726193")
			driver.find_element_by_class_name("login-btn").click()
			flag=2
			if flag==2:
				break
		except Exception as e:
			continue
	otp = int(input("Enter OTP"))
	driver.find_elements_by_class_name("mat-input-element")[0].send_keys(otp)
	time.sleep(2)
	driver.find_element_by_class_name("next-btn").click()
	time.sleep(5)
	elems = driver.find_elements_by_class_name("btnlist")
	#CHECK FOR MULTIPLE PEOPLE ON SAME NUMBER
	for elem in elems:
		if elem.text == 'Schedule':
			elem.click()
			break
	time.sleep(2)
	driver.find_elements_by_class_name("register-btn")[0].click()
	time.sleep(2)
	driver.find_element_by_id("mat-input-2").send_keys(pin)
	time.sleep(2)
	driver.find_elements_by_class_name("pin-search-btn")[0].click()
	time.sleep(5)
	##  Print request headers
	for request in driver.requests:
		if "appointment/sessions" in request.url:
			myurl = request.url # <--------------- Request url
			# print(request.headers) # <----------- Request headers
	driver.get(myurl)	


def get_cowin_dict_by_pin_by_selenium(pin,today=datetime.now(tz=gettz('Asia/Kolkata')).date().strftime("%d-%m-%Y")):
	if 'driver' not in globals():
		prepare_driver()
	else:
		driver.refresh()
	jsontxt = driver.find_element_by_tag_name("pre").text
	cowin_dict  = json.loads(jsontxt)
	return cowin_dict

def get_availaible_slots(cowin_dict):
	all_centres_list_of_dicts = cowin_dict["centers"]
	datels = []
	availablels = []
	agels = []
	typevacls = []
	feels = []
	centernamels = []
	
	for iter1, center_dict in enumerate(all_centres_list_of_dicts):
		pincode = center_dict["pincode"]
		center_district = center_dict["district_name"]
		center_name = center_dict["name"]
		center_state = center_dict["state_name"]
		fee_type = center_dict["fee_type"]
		private_center_dict = {}
		for iter2, session_dict in enumerate(center_dict["sessions"]):
			avail_date = session_dict["date"]
			avail_slots = session_dict["available_capacity"]
			slot_age_lim = session_dict["min_age_limit"]
			vaccine_type = session_dict["vaccine"]

			if required_vaccine_type == "ANY":
				if avail_slots > 0 and age>=slot_age_lim:
					availablels.append(avail_slots)
					datels.append(avail_date)
					agels.append(slot_age_lim)
					typevacls.append(vaccine_type)
					feels.append(fee_type)
					centernamels.append(f"{center_name} - {pincode}")
			else:
				if avail_slots > 0 and age>=slot_age_lim and vaccine_type==required_vaccine_type:
					availablels.append(avail_slots)
					datels.append(avail_date)
					agels.append(slot_age_lim)
					typevacls.append(vaccine_type)
					feels.append(fee_type)
					centernamels.append(f"{center_name} - {pincode}")



	return availablels, datels, agels, typevacls, centernamels,feels


name, age, receiver_email, pin, required_vaccine_type, bot_version, sleep_refresh,sleep_success, choice = start_up()

# ADD DISTRICT LATER
# if bot_version == 1.0 and search=="PIN":
if bot_version == 1.0:
	get_cowin_dict = get_cowin_dict_by_pin_by_api
elif bot_version == 2.0:
	get_cowin_dict = get_cowin_dict_by_pin_by_selenium

while True:
	try:
		cowin_dict = get_cowin_dict(pin)
		availablels, datels, agels, typevacls, centernamels,feels = get_availaible_slots(cowin_dict)

		if len(availablels) > 0:
			message = get_email_update_text(name, availablels, datels, agels, typevacls, centernamels, feels)
			send_email(receiver_email,message)
			print(message)
			print("\aEmail Sent Successfully. Sleeping for 1 hour")
			time.sleep(sleep_success)
		else:
			time.sleep(sleep_refresh)
	except Exception as e:
		print(e)
		time.sleep(sleep_refresh)
		continue