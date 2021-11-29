import requests

account = {"username": "test", "password": "kaas"}
r = requests.get("https://databasegip.herokuapp.com/accounts", json=account)
token = r.json()
print(token)
# r = requests.get("http://localhost:8000/pages/homepage", json={"token": token})
# print(r.text)

