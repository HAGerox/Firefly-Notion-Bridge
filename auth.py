from dotenv import load_dotenv
import os
import urllib.parse
import requests

load_dotenv()

SCHOOL_CODE = os.getenv('SCHOOL_CODE')
HOST = os.getenv('HOST')
DEVICE_ID = os.getenv('DEVICE_ID')
SECRET = os.getenv('SECRET')
APP_ID = "Firefly-Notion-Integration"

str = f"{HOST}/login/api/gettoken?ffauth_device_id={DEVICE_ID}&ffauth_secret&device_id={DEVICE_ID}&app_id={APP_ID}"
redirect = urllib.parse.quote(str, safe='~()*!\'')

login_url = f"{HOST}/login/login.aspx?prelogin={redirect}"

print("Please login to Firefly using the following link:")
print(login_url)
SECRET = input("Please enter the secret from the Firefly login page: ")