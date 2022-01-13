import os

import uvicorn
from cryptography.fernet import Fernet
from fastapi import FastAPI, Response, status, HTTPException
import sqlite3
import jwt
from pydantic import BaseModel
import time

SECRET = "b8e32c1e0a8c6af7b04b1fe193c4293e1c4af76e1456a683"
cipher_suite = Fernet(b"viGCeC-_tdTJxDb72yWIzFkI4VO5H-fIE9btMX6iTGE=")


class Account(BaseModel):
    username: str
    password: str


class NewAccount(BaseModel):
    current_password: str
    new_password: str
    token: str


class Token(BaseModel):
    token: str


class Process(BaseModel):
    applicationName: str
    processName: str
    jwt: str


class Application(BaseModel):
    applicationName: str
    jwt: str


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
    return {"username": account_dict["username"]}


@app.post("/accounts/login")
async def get_item(account: Account):
    account_dict = account.dict()
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
        return {"token": token, "username": account_dict["username"]}


@app.post("/pages/homepage")
async def get_homepage(token: Token):
    token_dict = token.dict()
    conn = sqlite3.connect("accounts.db")
    cur = conn.cursor()
    sql = "SELECT username FROM accounts WHERE token = ?"
    cur.execute(sql, [token_dict["token"]])
    for row in cur.fetchall():
        username = row[0]
        break
    conn.close()
    return {"username": username}


@app.post("/accounts/changepassword")
async def change_password(newAccount: NewAccount):
    account_dict = newAccount.dict()
    print(account_dict["token"])
    conn = sqlite3.connect("accounts.db")
    cur = conn.cursor()
    sql = "SELECT password FROM accounts where token=?"
    cur.execute(sql, [account_dict["token"]])
    for row in cur.fetchall():
        password = row[0]
        break
    print(password)
    if cipher_suite.decrypt(password) != account_dict["current_password"]:
        return {"status": 'nope'}
    sql = "UPDATE accounts SET password = ? WHERE token = ?"
    print(cipher_suite.encrypt(str.encode(account_dict["new_password"])))
    cur.execute(sql, [cipher_suite.encrypt(str.encode(account_dict["new_password"])), account_dict["token"]])
    conn.close()
    return {"status": "success"}


@app.post("/application/createApplication")
async def create_application(application: Application):
    application_dict = application.dict()
    conn = sqlite3.connect("accounts.db")
    cur = conn.cursor()
    sql = "INSERT INTO application(name) VALUES(?)"
    cur.execute(sql, [application_dict["name"]])
    sql = "INSERT INTO AccountApplicationConnection(IDAccount, IDApplication) VALUES((SELECT id FROM accounts WHERE token=?), ?)"
    cur.execute(sql, [application_dict["jwt"], cur.lastrowid])
    conn.close()
    return


@app.post("/application/{app_id}/process/createProcess", status_code=status.HTTP_201_CREATED)
async def add_process(app_id: str, process: Process, response: Response):
    app_id = {"app_id": app_id}
    process_dict = process.dict()
    conn = sqlite3.connect("accounts.db")
    cur = conn.cursor()
    sql = "SELECT token FROM accounts WHERE id IN (SELECT IDAccount FROM AccountApplicationConnection WHERE IDApplication = ?)"
    cur.execute(sql, [app_id])
    found = False
    for row in cur.fetchall():
        if row[0] == process_dict["jwt"]:
            found = True
            break
    if found is False:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return
    sql = "INSERT INTO process(AProcessName) VALUES(?)"
    cur.execute(sql, [process_dict["processName"]])
    sql = "INSERT INTO ApplicationProcessConnection(ApplicationID, ProcessID) VALUES ((SELECT IDApplication FROM application WHERE name=? AND and applicationID in (SELECT IDApplication FROM AccountApplicationConnection WHERE IDAccount=(SELECT id FROM accounts WHERE token=?))), ?)"
    cur.execute(sql, [process_dict["applicationName"], process_dict["jwt"], cur.lastrowid])
    conn.close()
    return


@app.post("/application/{app_id}/usage/startusage")
async def start_usage(app_id: str, token: Token, response: Response):
    app_id = {"app_id": app_id}
    token_dict = token.dict()
    conn = sqlite3.connect("accounts.db")
    cur = conn.cursor()
    sql = "SELECT token FROM accounts WHERE id IN (SELECT IDAccount FROM AccountApplicationConnection WHERE IDApplication = ?)"
    cur.execute(sql, [app_id])
    found2 = False
    for row in cur.fetchall():
        if token_dict["token"] == row[0]:
            found2 = True
            break
    if found2 is False:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return
    sql = "INSERT INTO usage(timeStart) VALUES(?)"
    cur.execute(sql, [time.time()])
    sql = "INSERT INTO ApplicationProcessConnection(ApplicationID, ProcessID) VALUES(?, ?)"
    cur.execute(sql, [app_id, cur.lastrowid])
    conn.close()
    return


if __name__ == '__main__':
    uvicorn.run(app)
