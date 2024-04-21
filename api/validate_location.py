import requests
import os
from flask_restful import Resource
from flask import jsonify
from requests.structures import CaseInsensitiveDict
from dotenv import load_dotenv


dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)


class GeoIpResource(Resource):
    def get(self, ip: str):
        headers = CaseInsensitiveDict()
        headers["Accept"] = "application/json"
        resp = requests.get(f"https://ipinfo.io/{ip}?token={os.getenv('IPINFO_API_KEY')}", headers=headers)
        if resp.status_code == 200 and ip != "127.0.0.1":
            ip_json = resp.json()
            return jsonify({'postcode': ip_json["postal"], 'coords': list(map(float, ip_json["loc"].split(","))),
                            'country': ip_json["country"]})
        elif ip == "127.0.0.1":
            return jsonify(resp.json())
        return jsonify({'status': f"Location for {ip} not found"})
