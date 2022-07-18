from flask import Flask, render_template
from datetime import datetime, timedelta
import requests
import os
import json
app = Flask(__name__)

# export 'BEARER_TOKEN'='<your_bearer_token>'
bearer_token = os.environ.get("BEARER_TOKEN")

# Pull tweets for hashtag from Twitter API

def bearer_oauth(r):
    """
    Method required by bearer token authentication.
    """

    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2RecentSearchPython"
    return r

def connect_to_endpoint(url, params):
    response = requests.get(url, auth=bearer_oauth, params=params)
    print(response.status_code)
    if response.status_code != 200:
        raise Exception(response.status_code, response.text)
    return response.json()

@app.route("/", methods=["GET", "POST"])
def home():
    search_url = "https://api.twitter.com/2/tweets/search/recent"
    query_params = {'query': '#tbt', 'tweet.fields': 'public_metrics', 'start_time': '2022-07-18T00:00:00Z'}

    json_response = connect_to_endpoint(search_url, query_params)
    data = json.dumps(json_response, indent=4, sort_keys=True)
    return render_template('home.html', data=data)

if __name__ == "__main__":
    app.debug = True
    app.run()
