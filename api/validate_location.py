import requests
import os
import json
from flask_restful import Resource
from flask import jsonify
from requests.structures import CaseInsensitiveDict
from dotenv import load_dotenv


dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)


class LocationResource(Resource):
    def get(self, address: str):
        url = f"https://api.geoapify.com/v1/geocode/search?text={address}&lang=ru&format=json" \
              f"&apiKey={os.getenv('GEO_APIFY_API_KEY')}"
        headers = CaseInsensitiveDict()
        headers["Accept"] = "application/json"
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            loc_json, locations = resp.json(), []
            for found_loc in loc_json['results']:
                locations.append(
                    {'status': found_loc["rank"]["confidence"],
                     'formatted_address': found_loc["formatted"],
                     'coords': [found_loc["lat"], found_loc["lon"]],
                     'postcode': found_loc["postcode"]})
            return jsonify({'results': locations})
        return jsonify({'status': f"Location {address} not found"})


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


class PostOfficeResource(Resource):
    def get(self, postal_code: str):
        resp = requests.post("http://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/postal_unit",
                             headers={
                                 "Content-Type": "application/json",
                                 "Accept": "application/json",
                                 "Authorization": "Token " + os.getenv("DADATA_API_KEY")
                             }, data=json.dumps({"query": postal_code}))
        if resp.status_code == 200:
            offices_json = resp.json()["suggestions"][0]["data"]
            return jsonify({'coords': [offices_json["geo_lat"], offices_json["geo_lon"]],
                            'address': offices_json["address_str"]})
        return jsonify({'status': f"Post office for {postal_code} not found"})
