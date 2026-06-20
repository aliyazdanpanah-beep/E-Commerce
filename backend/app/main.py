from fastapi import FastAPI

app = FastAPI()

@app.get('/api/')
async def get_all_data():
   return {'massage' : 'wellcom FastAPI'}

