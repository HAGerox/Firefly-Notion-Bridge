import os
from dotenv import load_dotenv
import logging
import requests
from bs4 import BeautifulSoup
import webbrowser
import urllib.parse
logger = logging.getLogger(__name__)

class FireflyUser():
    def __init__(self) -> None:
        load_dotenv()

        if os.getenv('SCHOOL_CODE') and os.getenv('HOST') and os.getenv('DEVICE_ID') and os.getenv('SECRET') and os.getenv('NOTION_TOKEN') and os.getenv('DATABASE_ID'):
            self.school_code = os.getenv('SCHOOL_CODE')            
            self.host = os.getenv('HOST')
            self.device_id = os.getenv('DEVICE_ID')            
            self.secret = os.getenv('SECRET')            
            self.notion_token = os.getenv('NOTION_TOKEN')            
            self.database_id = os.getenv('DATABASE_ID')
            self.app_id = "Firefly-Notion-Bridge"
        else:
            self.get_user_auth_info()

    def get_user_auth_info(self):
        # .env file is not complete, get entirely new credentials
        repeat_flag = True
        print("You do not have full valid credentials, follow the instructions to add credentials")
        while repeat_flag:
            print("Do you want to create new firefly and notion credentials? ([Y]es/[N]o)")
            if input().upper() == "Y":

                # get school_code and host url
                host_flag = False
                while not host_flag:
                    print("Input your school code, it can be found under account settings while logged into firefly")
                    school_code_input = input().upper()
                    print(f"Is this school code correct? ({school_code_input}) The school code should be capitalised. ([Y]es/[N]o)")
                    if input().upper() == "Y":
                        self.school_code = school_code_input

                        # get host url inlcuding protocol
                        school_code_url = f"https://appgateway.fireflysolutions.co.uk/appgateway/school/{self.school_code}"
                        request = requests.get(school_code_url)
                        soup = BeautifulSoup(request.text, 'xml')

                        if soup.find('response').get('exists') == 'true':
                            address = soup.find('address').get_text(strip=True)

                            if soup.find('address').get('ssl') == "true":
                                self.host = f"https://{address}"
                            else:
                                self.host = f"http://{address}"

                            print(self.host)
                            host_flag = True

                        print("Input a device id, this can be anything you want")
                        self.device_id = input()

                        secret_flag = False
                        while not secret_flag:
                            non_parsed_redirect = f"{self.host}/login/api/gettoken?ffauth_device_id={self.device_id}&ffauth_secret&device_id={self.device_id}&app_id={self.app_id}"
                            redirect = urllib.parse.quote(non_parsed_redirect, safe='~()*!\'')
                            authenticate_url = f"{self.host}/login/login.aspx?prelogin={redirect}"
                            
                            print("A web page will open when you press enter, if it does not open, open the following link in your browser:")
                            input()
                            print(authenticate_url)
                            webbrowser.open(authenticate_url)

                            print("Please enter the secret from the Firefly login page (It is the string of characters in between <secret>...</secret>)")
                            secret_input = input()

                            authenticate_secret_url = f"{self.host}/Login/api/verifytoken?ffauth_device_id={self.device_id}&ffauth_secret={secret_input}"
                            authenticate_secret_request = requests.get(authenticate_secret_url)
                            if authenticate_secret_request.json()['valid'] == "true":
                                self.secret = secret_input
                                secret_flag = True
                            
                            else:
                                print("Your secret did not work, please try again, and make sure you copy it correctly")

                repeat_flag = False
            else:
                print("""Do you want to:
                    [1] load your own .env file, format can be found on github
                    [2] create new firefly and notion credentials
                    [3] quit""")
                if input() == "1":
                    print("Add your .env file to the same directory as this file and save. Press return once you are done")
                    input()
                    return
                elif input() == "2":
                    continue
                else:
                    exit()

if __name__ == "__main__":
    user = FireflyUser()