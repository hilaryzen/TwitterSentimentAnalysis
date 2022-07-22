from flask import Flask, render_template
from datetime import datetime, timedelta
import requests
import os
import json
import pandas as pd
import numpy as np
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

def convert_tweets_json(json):
    """
    Convert JSON from Twitter API to a 2D array with text, domain, and metrics
    """
    columns = ['text', 'domain_name', 'domain_desc', 'likes', 'quotes', 'replies', 'retweets']
    data = []
    for tweet in json['data']:
        # print(tweet.keys())
        info = [tweet['text'], tweet['context_annotations'][0]['domain']['name'], tweet['context_annotations'][0]['domain']['description'], tweet['public_metrics']['like_count'], tweet['public_metrics']['quote_count'], tweet['public_metrics']['reply_count'], tweet['public_metrics']['retweet_count']]
        data.append(info)
    return columns, data

@app.route("/", methods=["GET", "POST"])
def home():
    search_url = "https://api.twitter.com/2/tweets/search/recent"
    start_time = datetime.now() - timedelta(days=1)
    start_time = start_time.isoformat('T', 'seconds') + 'Z'
    # Add max_results as a param to increase tweets to 100
    query_params = {'query': '#tbt lang:en', 'tweet.fields': 'context_annotations,public_metrics', 'start_time': start_time}

    json_response = connect_to_endpoint(search_url, query_params)
    # data = json.dumps(json_response, indent=4, sort_keys=True)
    columns, data = convert_tweets_json(json_response)
    return render_template('home.html', data=data)

if __name__ == "__main__":
    app.debug = True
    app.run()
