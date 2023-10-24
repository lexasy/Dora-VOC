import sqlite3
import hashlib
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()


@app.get("/signup/", response_class=JSONResponse)
async def create_user(login: str, password: str, repeat_password: str, name: str, surname: str, email: str):
    if (password == repeat_password) and len(password) >= 6:
        try:
            with sqlite3.connect('/db/user.db') as db:
                cur = db.cursor()
                query = f"""INSERT INTO users (name,surname,email,login,password) VALUES ('{name}', '{surname}', '{email}', '{login}', '{(hashlib.md5(bytes(password, 'utf-8'))).hexdigest()}')"""
                cur.execute(query)
                db.commit()
                cur.execute("""SELECT * from users;""")
                records_user = cur.fetchall()
                
            return JSONResponse({"status": True, "login": [user[3] for user in records_user if user[3] == login]})
        except sqlite3.IntegrityError:
            return JSONResponse({"status": False, "description": "user with the same login already exists"})
    return JSONResponse({"status": False, "description": "your passwods are not same or less 6 symbols, please, get another try"})


@app.get("/login/", response_class=JSONResponse)
async def login(login: str, password: str):
    with sqlite3.connect('/db/user.db') as db:
        cur = db.cursor()
        query = f"""SELECT login FROM users WHERE login = '{login}'"""
        cur.execute(query)
        records_login = cur.fetchall()
    if records_login != []:
        with sqlite3.connect('/db/user.db') as db:
            cur = db.cursor()
            query = f"""SELECT password FROM users WHERE login = '{login}'"""
            cur.execute(query)
            records_password = cur.fetchall()
        if (hashlib.md5(bytes(password, 'utf-8'))).hexdigest() == records_password[0][0]:
            return JSONResponse({"status": True, "response": f"Welcome {records_login[0][0]}"})
        return JSONResponse({"status": False, "description": "your password is incorrect"})
    return JSONResponse({"status": False, "description": "user with the same login does not exist yet"})


if __name__ == '__main__':
    uvicorn.run(app='main:app', host='0.0.0.0', port=5300)