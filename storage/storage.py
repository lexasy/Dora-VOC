import os
import pathlib
import uvicorn

from shutil import copyfileobj, rmtree

from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import FileResponse, JSONResponse

app = FastAPI()

@app.post('/upload/{filename}', response_class=JSONResponse)
async def upload_file(filename: str, file: UploadFile = File(...)):
    try:
        with open(f'files/{filename}', 'wb') as data:
            copyfileobj(file.file, data)
        return {'message': 'OK'}
    except Exception as error:
        return {'message': f'{error}'}


@app.get('/delete/{filename}', response_class=JSONResponse)
async def delete_file(filename: str):
    if(os.path.exists(f'files/{filename}')):
        os.remove(f'files/{filename}')
    return {'message': 'OK'}


@app.get('/{filename}', response_class=FileResponse)
async def get_file(filename: str):
    if(os.path.exists(f'files/{filename}')):
        # file_extension = pathlib.Path(f'files/{filename}').suffix
        return FileResponse(path=f'files/{filename}', media_type='application/octet-stream')
    return {'message': 'file not found'}


@app.get('/exists/{filename}', response_class=JSONResponse)
async def is_file_exist(filename: str):
    return {'message': int(os.path.exists(f'files/{filename}'))}


@app.get('/purge/{request_id}', response_class=JSONResponse)
async def purge_request_data(request_id: str):
    try:
        rmtree(path=f'files/{request_id}', ignore_errors=True)
        for file in ['rgb', 'final', 'depth']:
            path = f'files/{request_id}_{file}.mp4'
            if(os.path.exists(path)):
                os.remove(path=path)
        os.remove(f'files/{request_id}_status.txt')
        os.remove(f'files/{request_id}.bag')
        return JSONResponse({'message': 'OK'})
    except Exception as error:
        return JSONResponse({'message': f'{error}'})


@app.get('/status/{request_id}', response_class=JSONResponse)
async def get_request_status(request_id: str, request: Request):
    filename = f'files/{request_id}_status.txt'
    if(not os.path.exists(filename)):
        return JSONResponse({'status': 'Starting...'})
    with open(filename) as sf:
        status = sf.readline()
        return JSONResponse({'status': status})


if __name__ == '__main__':
    uvicorn.run(app='storage:app', port=4300, host='0.0.0.0')