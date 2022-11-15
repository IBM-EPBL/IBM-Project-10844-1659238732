import os
import base64
import DateTime
import requests
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def main():
    headers_list = request.headers.getlist("X-Forwarded-For")
    user_ip = headers_list[0] if headers_list else request.remote_addr
    if user_ip == "127.0.0.1":
        user_ip = ""

    url = f"http://ip-api.com/json/{user_ip}?fields=status,message,continent,continentCode,country,countryCode,region,regionName,city,district,zip,lat,lon,timezone,offset,currency,isp,org,as,asname,reverse,mobile,proxy,hosting,query"
    response = requests.get(url)
    result = response.json()
    if result.get("status") == "fail":
        return jsonify(result)

    if 200 <= response.status_code < 300:
        ip = result.get("query")
        ip_bytes = ip.encode("ascii")
        return jsonify(
            ip = ip,
            location = result.get('location'),
            lat = result.get('lat'),
            lon = result.get('lon'),
            timestamp = datetime.now(),
            base64OfIP = str(base64.b64encode(ip_bytes))
        )
    else:
        return jsonify(result)

if __name__ == '__main__':
    app.run(debug = False if os.environ.get('DEBUG') == 'False' else True)