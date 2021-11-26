import os

import uvicorn
from cryptography.fernet import Fernet
from fastapi import FastAPI
import sqlite3
import jwt
from pydantic import BaseModel

SECRET = "b8e32c1e0a8c6af7b04b1fe193c4293e1c4af76e1456a683"
cipher_suite = Fernet(b"viGCeC-_tdTJxDb72yWIzFkI4VO5H-fIE9btMX6iTGE=")


class Item(BaseModel):
    username: str
    password: str


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/accounts")
async def create_item(item: Item):
    item_dict = item.dict()
    conn = sqlite3.connect("accounts.db")
    cur = conn.cursor()
    sql = "INSERT INTO accounts(username, password, token) VALUES(?, ?, ?)"
    encoded_jwt = jwt.encode({"username": item_dict["username"], "password": item_dict["password"]}, SECRET,
                             algorithm="HS256")
    params = [item_dict["username"], cipher_suite.encrypt(str.encode(item_dict["password"])), encoded_jwt]
    cur.execute(sql, params)
    conn.commit()
    conn.close()
    return 200


@app.get("/accounts")
async def get_item(item: Item):
    item_dict = item.dict()
    conn = sqlite3.connect("accounts.db")
    cur = conn.cursor()
    sql = "SELECT password FROM accounts WHERE username = ?"
    cur.execute(sql, [item_dict["username"]])
    for row in cur.fetchall():
        password = row[0]
        break
    print(password)
    if cipher_suite.decrypt(password) == str.encode(item_dict["password"]):
        sql = "SELECT token FROM accounts WHERE username = ?"
        cur.execute(sql, [item_dict["username"]])
        for row in cur.fetchall():
            token = row[0]
            break
        conn.close()
        return token


if __name__ == '__main__':
    uvicorn.run(app)
