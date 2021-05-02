"""
Author: Siddharth Chaini
Date: 02 May 2021
"""

import requests
import json
import smtplib, ssl
from email.message import EmailMessage
import os
from datetime import datetime
from dateutil.tz import gettz
import time
import getpass

password = getpass.getpass("Enter password for cowinpython@gmail.com: ")

def send_slot_email(receiver_email,message):
	port = 465  # For SSL
	smtp_server = "smtp.gmail.com"
	sender_email = "cowinpython@gmail.com"  # Enter your address
	msg = EmailMessage()
	msg.set_content(message)
	msg['Subject'] = f"COWINPy Update - {datetime.now(tz=gettz('Asia/Kolkata'))} IST"
	msg['From'] = sender_email
	msg['To'] = receiver_email
	context = ssl.create_default_context()
	with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
		server.login(sender_email, password)
		server.send_message(msg)


pref_file = "preferences.txt"
if os.path.isfile(pref_file):
	with open(pref_file,"r") as fp:
		pref_dict = fp.read()
		pref_dict = json.loads(pref_dict)
else:
	print("The file 'preferences.txt' was not found. Creating a new one. Please enter the following details:")
	with open(pref_file, "w") as fp:
		pref_dict = {}
		pref_dict["pin"] = int(input("Enter your pincode: "))
		pref_dict["receiver_email"] = input("Enter email id to which email will be sent: ")
		pref_dict["age"] = int(input("Enter your age: "))
		pref_dict["name"] = input("Enter your name: ")
		json.dump(pref_dict, fp, indent=4)


pin = pref_dict["pin"]
receiver_email = pref_dict["receiver_email"]
age = pref_dict["age"]
name = pref_dict["name"]

print("Retrieved all details...")

time.sleep(3)

start_message = f'''Dear {name},
Thank you for registering with COWINPy. This is an example email. You will get an email like this if any slots are available.
Please note that a maximum of 1 email will be sent every hour to prevent spam.

Regards,
Team COWINPy'''

send_slot_email(receiver_email,start_message)
print("Sent intro email")

while True:
	today = datetime.now(tz=gettz('Asia/Kolkata')).date().strftime("%d-%m-%Y")
	url = f"https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByPin?pincode={pin}&date={today}"
	cowin_dict = json.loads(requests.get(url).text)

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

			if avail_slots > 0 and age>=slot_age_lim:
				availablels.append(avail_slots)
				datels.append(avail_date)
				agels.append(slot_age_lim)
				typevacls.append(vaccine_type)
				feels.append(fee_type)
				centernamels.append(center_name)

				if (iter1 == len(all_centres_list_of_dicts) - 1) and (iter2 == len(center_dict["sessions"]) - 1):
					message =f'''Dear {name},
There are {availablels} TOTAL slots you can book right now for {datels}, age limit = {agels}!
Book soon!

Available capacity:\t{availablels}
Age:\t{agels} and above.
Date:\t{datels}
Vaccine:\t{typevacls}
Center:\t{centernamels}, {center_district}, {center_state} - {pincode}
Fee Type:\t{feels}.

Please check https://www.cowin.gov.in/home for more details!

Regards,
Team COWINPy
'''
					send_slot_email(receiver_email,message)
					print(message)
					print("Email Sent Successfully. Sleeping for 1 hour")
					time.sleep(3600)
	print(time.sleep(10))

print("Exiting.")