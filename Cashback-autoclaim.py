import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta
from Credential import EE_username, EE_password, Fonehouse_username, Fonehouse_password, order_number, date_of_birth, mobile_number
import os

last_bill = date.today().replace(day=1) - timedelta(days=1)
bill_date = f"{last_bill.year}-{last_bill.month}-26"

header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"}


filename = f"{bill_date}.pdf"


class EE:
    payload = {"username": EE_username,
               "password": EE_password,
               "requestId": "",
               }

    web_page = "https://myaccount.ee.co.uk/app/my-bills-and-payments"

    def __init__(self):
        self.soup = None

    def get_requestId(self, link, session):
        request = session.get(link).content
        soup = BeautifulSoup(request, 'html.parser')
        try:
            self.payload['requestId'] = soup.find("input", id="requestId")['value']
        except TypeError:
            self.payload['requestId'] = soup.find("input", id="csrf")['value']

    def login(self):
        with requests.Session() as session:
            request = session.get(self.web_page).content
            self.get_requestId(self.web_page, session)
            print("Attempting to login...")
            login = session.post("https://api.ee.co.uk/v1/identity/authorize/login", data=self.payload,
                                 headers=header)

            """Check if the credential provided is correct"""
            if "Login error" in login.text:
                print("Incorrect EE Username or Password ")
            else:
                print("Login Successful")
                self.get_bill(session)
                Fonehouse()

    def get_bill(self, session):

        self.get_requestId(self.web_page, session)  # retrieve new token after logging in

        payload = {"fa": "pdf",
                   "billId": bill_date,
                   "csrf": self.payload['requestId'],
                   }
        with open(f'{payload["billId"]}.pdf', 'wb') as f:
            f.write(session.post(self.web_page, data=payload, headers=header).content)
            print(f"Latest bill has been downloaded: {filename}")


class Fonehouse:
    payload = {"email": Fonehouse_username,
               "password": Fonehouse_password,
               "_token": "", }

    web_page = "https://www.fonehouse.co.uk/"

    cash_back = "https://www.fonehouse.co.uk/user/cashback-redemption"

    def __init__(self):
        self.soup = None
        self.login()

    def login(self):
        with requests.Session() as session:
            request = session.get(self.web_page).text
            self.get_token(self.web_page, session)
            login = session.post("https://www.fonehouse.co.uk/login", data=self.payload,
                                 headers=header)

            if "These credentials do not match our records" in login.text:
                print("Incorrect Fonehouse Email or Password ")
            else:
                print("Fonehouse Login Successful")
                self.upload_file(session)

    def get_token(self, link, session):
        request = session.get(link).content
        self.soup = BeautifulSoup(request, 'html.parser')
        self.payload['_token'] = self.soup.find("input", type="hidden")['value']

    def upload_file(self, session):

        self.get_token(self.cash_back, session)

        payload = {
            "_token": self.payload["_token"],
            "_token": self.payload["_token"],
            "order_number": order_number,
            "date_of_birth": date_of_birth,
            "tariff_provider_id": 1,
            "mobile_number": mobile_number,
            "bill_date": bill_date,

        }

        file = {"bill_file": (filename, open(filename, "rb").read())
                }

        print("Uploading bill to Fonehouse")
        #session.post(self.cash_back, files=file, data=payload)
        print("Cash back claimed")


ee = EE()

if filename not in os.listdir():
    print('File not found... Attempting to download')
    ee.login()
else:
    Fonehouse()
