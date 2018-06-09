import requests
import json
r = requests.post('http://127.0.0.1:8001', files={'file': open('1.png')}, data={'project': 'ipe'})
print r.json()
