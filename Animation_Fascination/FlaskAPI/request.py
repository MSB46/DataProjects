import requests
from app_input import data_in

URL = 'http://127.0.0.1:5000/predict'
header = {'Content-Type: application/json'}
data = {'input':data_in}

r= requests.get(URL,headers=header,json=data)

r.json
