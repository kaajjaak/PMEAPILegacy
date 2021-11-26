import os

import uvicorn
from cryptography.fernet import Fernet
from fastapi import FastAPI, Response, status
import sqlite3
import jwt
from pydantic import BaseModel

SECRET = "b8e32c1e0a8c6af7b04b1fe193c4293e1c4af76e1456a683"
cipher_suite = Fernet(b"viGCeC-_tdTJxDb72yWIzFkI4VO5H-fIE9btMX6iTGE=")


class Account(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    token: str


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/accounts")
async def create_account(account: Account, response: Response):
    account_dict = account.dict()
    conn = sqlite3.connect("accounts.db")
    cur = conn.cursor()
    sql = "INSERT INTO accounts(username, password, token) VALUES(?, ?, ?)"
    encoded_jwt = jwt.encode({"username": account_dict["username"], "password": account_dict["password"]}, SECRET,
                             algorithm="HS256")
    params = [account_dict["username"], cipher_suite.encrypt(str.encode(account_dict["password"])), encoded_jwt]
    cur.execute(sql, params)
    conn.commit()
    conn.close()
    response.status_code = status.HTTP_201_CREATED
    return account_dict["username"]


@app.get("/accounts")
async def get_item(account: Account):
    account_dict = account.dict()
    print(account_dict)
    conn = sqlite3.connect("accounts.db")
    cur = conn.cursor()
    sql = "SELECT password FROM accounts WHERE username = ?"
    cur.execute(sql, [account_dict["username"]])
    for row in cur.fetchall():
        password = row[0]
        break
    if cipher_suite.decrypt(password) == str.encode(account_dict["password"]):
        sql = "SELECT token FROM accounts WHERE username = ?"
        cur.execute(sql, [account_dict["username"]])
        for row in cur.fetchall():
            token = row[0]
            break
        conn.close()
        return token


@app.get("/pages/homepage")
async def get_homepage(token: Token):
    token_dict = token.dict()
    conn = sqlite3.connect("accounts.db")
    cur = conn.cursor()
    sql = "SELECT username FROM accounts WHERE token = ?"
    cur.execute(sql, [token_dict["token"]])
    username = cur.fetchone()[0]
    conn.close()
    return {"username": username}


if __name__ == '__main__':
    uvicorn.run(app)
