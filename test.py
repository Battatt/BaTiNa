import requests

response = requests.get(f'http://127.0.0.1:{5000}/api/items')
print(response.json())
