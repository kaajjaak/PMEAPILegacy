import requests

account = {"username": "test", "password": "kaas"}
r = requests.post("http://localhost:8000/accounts", json=account)
print(r.text)
