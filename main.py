import random
import os
import pika
import requests
import uvicorn

from typing import Annotated, List

from fastapi import FastAPI, File, UploadFile, Request, Form, status, Cookie
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Create FastAPI application
app = FastAPI()

# Define static files and templates storage
app.mount('/static', StaticFiles(directory='static'), name='static')
templates = Jinja2Templates(directory="templates")


@app.get('/', response_class=HTMLResponse)
async def load_welcome_page(request: Request):
    return templates.TemplateResponse('welcome.html', {'request': request})


@app.get('/start', response_class=HTMLResponse)
async def load_start_page(request: Request, user: str | None = Cookie(default=None)):
    if user is None:
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse('video.html', {'request': request})


@app.get('/login')
async def load_login_page(request: Request, user: str | None = Cookie(default=None)):
    if user is not None:
        return RedirectResponse("/start", status_code=303)
    return templates.TemplateResponse('login.html', {'request': request})


@app.post('/login', response_class=RedirectResponse)
async def login(request: Request, login: Annotated[str, Form()], password: Annotated[str, Form()]):
    response = None
    r = requests.get('http://db:5300/login', {'login': login, 'password': password})
    if r.json()['status'] == True:
        response = RedirectResponse('/start', status_code=303)
        response.set_cookie(key='user', value=login)
    else:
        response = templates.TemplateResponse("login.html", {"request": request, "error": r.json()["description"]})
    return response


@app.get('/logout', response_class=RedirectResponse)
async def logout(user: str | None = Cookie(default=None)):
    response = RedirectResponse('/', status_code=303)
    if user is not None:
        response.delete_cookie(key='user')
    return response


@app.get('/signup')
async def load_signup_page(request: Request, user: str | None = Cookie(default=None)):
    if user is not None:
        return RedirectResponse("/start", status_code=303)
    return templates.TemplateResponse('registration.html', {'request': request})


@app.post('/signup')
async def signup(request: Request, name: Annotated[str, Form()], surname: Annotated[str, Form()], login: Annotated[str, Form()], email: Annotated[str, Form()], password: Annotated[str, Form()], repeat_password: Annotated[str, Form()]):
    response = None
    r = requests.get('http://db:5300/signup', {'login': login, 'password': password, 'repeat_password': repeat_password, 'name': name, 'surname': surname,  'email': email})
    print(r.json())
    if r.json()['status'] == True:
        response = RedirectResponse('/login', status_code=303)
    else:
        response = templates.TemplateResponse("registration.html", {"request": request, "error": r.json()["description"]})
    return response


@app.post('/start')
async def upload_and_start(request: Request, file: UploadFile = File(...)):
    try:
        request_id = ''.join(random.choice('0123456789abcdef') for _ in range(12))
        requests.post(url=f'http://storage:4300/upload/{request_id}.bag', files={'file': file.file})
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
        channel = connection.channel()
        channel.queue_declare(queue='tasks', durable=True)
        channel.basic_publish(
            exchange='',
            routing_key='tasks',
            body=request_id,
            properties=pika.BasicProperties(delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE))
        connection.close()
        return RedirectResponse(url=f'/request/{request_id}', status_code=status.HTTP_303_SEE_OTHER)
    except Exception as error:
        return JSONResponse({'message': f'An error occured: {error}'})


@app.get('/request/{request_id}', response_class=HTMLResponse)
async def process_request(request: Request, request_id: str, user: str | None = Cookie(default=None)):
    if user is None:
        return RedirectResponse("/login", status_code=303)
    
    r = requests.get(f'http://storage:4300/status/{request_id}')
    status = r.json()['status']

    if status == 'Finished':
        return templates.TemplateResponse('content.html', context={
                                            'request': request, 
                                            'final_path': f"http://127.0.0.1:4300/{request_id}_final.mp4",
                                            'rgb_path': f"http://127.0.0.1:4300/{request_id}_rgb.mp4",
                                            'depth_path': f"http://127.0.0.1:4300/{request_id}_depth.mp4",
                                            'close': f'/close/{request_id}'
                                            })
    elif status == 'Error':
        return RedirectResponse('/start', status_code=303)
    else:
        return templates.TemplateResponse('success.html', context={'request': request, 'request_id': request_id, 'status': status})


@app.get('/close/{request_id}', response_class=RedirectResponse)
async def close_request(request: Request, request_id: str):
    try:
        requests.get(url=f"http://storage:4300/purge/{request_id}")
    except Exception as error:
        print(f'[ERROR]: Unable to purge request #{request_id} data: {error}')
    return RedirectResponse(url=f'/start', status_code=status.HTTP_303_SEE_OTHER)


if __name__ == '__main__':
    uvicorn.run(app='main:app', host='0.0.0.0', port=8000)