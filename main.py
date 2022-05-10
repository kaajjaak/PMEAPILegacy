import os

import uvicorn
from cryptography.fernet import Fernet
from fastapi import FastAPI, Response, status, HTTPException
import sqlite3
import mysql.connector
import jwt
from pydantic import BaseModel
import time
import json

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


class Limit(BaseModel):
    token: str
    applicationID: int
    limit: int


app = FastAPI()


def start_connection():
    return mysql.connector.connect(user='ID191774_6itngip3',
                                   password='BhJNVQ2i',
                                   host='ID191774_6itngip3.db.webhosting.be',
                                   database='ID191774_6itngip3')


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/accounts")
async def create_account(account: Account, response: Response):
    account_dict = account.dict()
    conn = start_connection()
    cur = conn.cursor()
    sql = "INSERT INTO accounts(username, password, token) VALUES(%s, %s, %s)"
    encoded_jwt = jwt.encode({"username": account_dict["username"], "password": account_dict["password"]}, SECRET,
                             algorithm="HS256")
    params = [account_dict["username"], cipher_suite.encrypt(str.encode(account_dict["password"])), encoded_jwt]
    cur.execute(sql, params)
    conn.commit()
    conn.close()
    response.status_code = status.HTTP_201_CREATED
    return {"username": account_dict["username"], "token": encoded_jwt}


@app.post("/accounts/login")
async def get_item(account: Account, response: Response):
    account_dict = account.dict()
    conn = start_connection()
    cur = conn.cursor()
    sql = "SELECT password FROM accounts WHERE username = %s"
    cur.execute(sql, [account_dict["username"]])
    for row in cur.fetchall():
        password = row[0]
        break
    try:
        if cipher_suite.decrypt(bytes(password, 'utf-8')) == str.encode(account_dict["password"]):
            sql = "SELECT token FROM accounts WHERE username = %s"
            cur.execute(sql, [account_dict["username"]])
            for row in cur.fetchall():
                token = row[0]
                break
            conn.close()
            response.status_code = status.HTTP_202_ACCEPTED
            return {"token": token, "username": account_dict["username"]}
        else:
            response.status_code = status.HTTP_401_UNAUTHORIZED
            conn.close()
            return
    except UnboundLocalError:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        conn.close()
        return


@app.post("/pages/homepage")
async def get_homepage(token: Token):
    token_dict = token.dict()
    conn = start_connection()
    cur = conn.cursor()
    sql = "SELECT username FROM accounts WHERE token = %s"
    cur.execute(sql, [token_dict["token"]])
    for row in cur.fetchall():
        username = row[0]
        break
    conn.close()
    return {"username": username}


@app.post("/accounts/changepassword")
async def change_password(newAccount: NewAccount):
    account_dict = newAccount.dict()
    conn = start_connection()
    cur = conn.cursor()
    sql = "SELECT password FROM accounts where token=%s"
    cur.execute(sql, [account_dict["token"]])
    for row in cur.fetchall():
        password = row[0]
        break
    if cipher_suite.decrypt(password).decode("utf-8") != account_dict["current_password"]:
        return {"status": 'nope'}
    sql = "UPDATE accounts SET password = ? WHERE token = %s"
    cur.execute(sql, [cipher_suite.encrypt(str.encode(account_dict["new_password"])), account_dict["token"]])
    conn.commit()
    conn.close()
    return {"status": "success"}


@app.post("/application/createApplication")
async def create_application(application: Application, response: Response):
    application_dict = application.dict()
    conn = start_connection()
    cur = conn.cursor()
    sql = "INSERT INTO application(name) VALUES(%s)"
    cur.execute(sql, [application_dict["applicationName"]])
    sql = "INSERT INTO AccountApplicationConnection(IDAccount, IDApplication) VALUES((SELECT id FROM accounts WHERE token=%s), %s)"
    rowidvalue = cur.lastrowid
    cur.execute(sql, [application_dict["jwt"], rowidvalue])
    conn.commit()
    response.status_code = status.HTTP_201_CREATED
    conn.close()
    return {"id": rowidvalue}


@app.post("/application/applicationList")
async def list_applications(token: Token, response: Response):
    token_dict = token.dict()
    conn = start_connection()
    cur = conn.cursor()
    sql = "SELECT name, applicationID FROM application app WHERE (app.applicationID IN (SELECT ApplicationID FROM AccountApplicationConnection appc WHERE appc.IDAccount in (SELECT id FROM accounts idd WHERE idd.token = %s)))"
    cur.execute(sql, [token_dict["token"]])
    applications = cur.fetchall()
    print(applications)
    applications_json = []
    for application in applications:
        applications_json.append({"application": {"name": application[0], "id": application[1]}})
    print(applications_json)
    response.status_code = status.HTTP_202_ACCEPTED
    conn.close()
    return applications_json


@app.post("/application/{app_id}/process/createProcess")
async def add_process(app_id: int, process: Process, response: Response):
    process_dict = process.dict()
    conn = start_connection()
    cur = conn.cursor()
    sql = "SELECT token FROM accounts WHERE id IN (SELECT IDAccount FROM AccountApplicationConnection WHERE IDApplication = %s)"
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
    sql = "INSERT INTO ApplicationProcessConnection(ApplicationID, ProcessID) VALUES ((SELECT applicationID FROM application WHERE name=? AND applicationID in (SELECT IDApplication FROM AccountApplicationConnection WHERE IDAccount=(SELECT id FROM accounts WHERE token=%s))), %s)"
    cur.execute(sql, [process_dict["applicationName"], process_dict["jwt"], cur.lastrowid])
    conn.commit()
    conn.close()
    response.status_code = status.HTTP_201_CREATED
    return


@app.post("/application/{app_id}/processList")
async def list_process(app_id: int, token: Token, response: Response):
    token_dict = token.dict()
    conn = start_connection()
    cur = conn.cursor()
    sql = "SELECT IDProcess, AProcessName FROM process WHERE IDProcess IN (SELECT ProcessID FROM ApplicationProcessConnection WHERE ApplicationID IN (SELECT IDApplication FROM AccountApplicationConnection WHERE IDAccount = (SELECT id FROM accounts WHERE token = %s)) AND ApplicationID = %s)"
    cur.execute(sql, [token_dict["token"], app_id])
    processes = cur.fetchall()
    processes_json = []
    for process in processes:
        processes_json.append({"process": {"id": process[0], "name": process[1]}, "id": app_id})
    response.status_code = status.HTTP_202_ACCEPTED
    conn.close()
    return processes_json


@app.post("/application/{app_id}/usage/startUsage")
async def start_usage(app_id: int, token: Token, response: Response):
    token_dict = token.dict()
    conn = start_connection()
    cur = conn.cursor()
    sql = "SELECT token FROM accounts WHERE id IN (SELECT IDAccount FROM AccountApplicationConnection WHERE IDApplication = %s)"
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
    sql = "INSERT INTO ApplicationProcessConnection(ApplicationID, ProcessID) VALUES(%s, %s)"
    cur.execute(sql, [app_id, cur.lastrowid])
    conn.commit()
    conn.close()
    return


@app.post("/application/{app_id}/usage/endUsage")
async def end_usage(app_id: int, token: Token, response: Response):
    token_dict = token.dict()
    conn = start_connection()
    cur = conn.cursor()
    sql = "UPDATE usage SET timeEnd = %s WHERE (IDUsage in (SELECT UsageID FROM ApplicationUsageConnection WHERE ApplicationID in (SELECT IDApplication FROM AccountApplicationConnection  WHERE IDAccount IN (SELECT id FROM accounts WHERE token = %s)) AND ApplicationID = %s))"
    cur.execute(sql, [time.time(), token_dict["token"], app_id])
    conn.commit()
    conn.close()
    return


@app.post("/application/{app_id}/limits/createlimit")
async def create_limit(app_id: int, limit: Limit, response: Response):
    conn = start_connection()
    cur = conn.cursor()
    sql = "SELECT token FROM accounts WHERE id IN (SELECT IDAccount FROM AccountApplicationConnection WHERE IDApplication = %s)"
    cur.execute(sql, [app_id])
    found2 = False
    for row in cur.fetchall():
        if limit.token == row[0]:
            found2 = True
            break
    if found2 is False:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return
    sql = "INSERT INTO limit(LimitApplicationID, limitTime) VALUES(%s, %s)"
    cur.execute(sql, [limit.applicationID, limit.limit])
    conn.commit()
    conn.close()
    return


if __name__ == '__main__':
    uvicorn.run(app)
