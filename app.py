from flask import Flask, render_template, request
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
    # print(json)
    columns = ['text', 'domain_name', 'domain_desc', 'likes', 'quotes', 'replies', 'retweets']
    data = []
    for tweet in json['data']:
        # print(tweet.keys())
        if 'context_annotations' in tweet.keys():
            info = [tweet['text'], tweet['context_annotations'][0]['domain']['name'], tweet['context_annotations'][0]['domain']['description'], tweet['public_metrics']['like_count'], tweet['public_metrics']['quote_count'], tweet['public_metrics']['reply_count'], tweet['public_metrics']['retweet_count']]
        else:
            info = [tweet['text'], 'N/A', 'N/A', tweet['public_metrics']['like_count'], tweet['public_metrics']['quote_count'], tweet['public_metrics']['reply_count'], tweet['public_metrics']['retweet_count']]
        data.append(info)
    return columns, data

@app.route("/", methods=["GET", "POST"])
def home():
    return render_template('home.html')

@app.route("/search", methods=["GET", "POST"])
def search():
    # Get searched hashtag
    hashtag = request.form['hashtag']

    search_url = "https://api.twitter.com/2/tweets/search/recent"
    start_time = datetime.now() - timedelta(days=1)
    start_time = start_time.isoformat('T', 'seconds') + 'Z'
    query = hashtag.strip() + ' lang:en'
    # Add max_results as a param to increase tweets to 100
    query_params = {'query': query, 'tweet.fields': 'context_annotations,public_metrics', 'start_time': start_time}

    json_response = connect_to_endpoint(search_url, query_params)
    columns, data = convert_tweets_json(json_response)
    # data = [['RT @foodietechlab: [homemade] Flank steak with chimichurri #viral #trending #foodie #foodblogger #foodphotography #ff #tbt #ico https://t.c…', 'Digital Assets & Crypto', 'For cryptocurrency entities', 0, 0, 0, 24], ['RT @foodietechlab: [Homemade] Polish/Carpathian Cream Cake (Karpatka). #viral #trending #foodie #foodblogger #foodphotography #ff #tbt #ico…', 'Entities [Entity Service]', 'Entity Service top level domain, every item that is in Entity Service should be in this domain', 0, 0, 0, 35], ['RT @foodietechlab: [homemade] Ham &amp; Cheese Rolls #viral #trending #foodie #foodblogger #foodphotography #ff #tbt #ico https://t.co/nmcmveT0…', 'Digital Assets & Crypto', 'For cryptocurrency entities', 0, 0, 0, 34], ['#mimicabbatti WAD-FM\n\n#TBT Having a son with a\nWay-Older-guy , \nonly to have your son ask you, \n“How’s the old-man doing ?”\nWould be the joke of a lifetime. \nTony would forever Revel in that joke. https://t.co/tZSbgNFwPK', 'Reoccurring Trends', 'Twitter generated Trends that occur on a daily, weekly, monthly, or yearly basis', 0, 0, 0, 0], ['RT @foodietechlab: [Homemade] egg rolls. #viral #trending #foodie #foodblogger #foodphotography #ff #tbt #ico https://t.co/tsxPUa6K4i', 'Digital Assets & Crypto', 'For cryptocurrency entities', 0, 0, 0, 3], ['RT @tushyraw: #TBT to this stunning @sarah_sultry moment 🔥 What moment do you think back on most? https://t.co/Uu1ZfQrFM9', 'Reoccurring Trends', 'Twitter generated Trends that occur on a daily, weekly, monthly, or yearly basis', 0, 0, 0, 28], ['RT @gethypedllc: Please retweet and follow me @gethypedllc\n#funny #mondaymotivation #tbt #thursdaythoughts #influencermarketing #fridayfeel…', 'Reoccurring Trends', 'Twitter generated Trends that occur on a daily, weekly, monthly, or yearly basis', 0, 0, 0, 1], ['RT @foodietechlab: [Homemade] egg rolls. #viral #trending #foodie #foodblogger #foodphotography #ff #tbt #ico https://t.co/tsxPUa6K4i', 'Digital Assets & Crypto', 'For cryptocurrency entities', 0, 0, 0, 3], ['Please retweet and follow me @gethypedllc\n#funny #mondaymotivation #tbt #thursdaythoughts #influencermarketing #fridayfeeling #influencer #explorepage #viral #trending', 'Reoccurring Trends', 'Twitter generated Trends that occur on a daily, weekly, monthly, or yearly basis', 0, 0, 0, 1], ['RT @Edyellofficial: Keep you Noise out, and get your truly immersive sound in.🎶🎵\n\n#competition #influencer #influencermarketing #fridayfeel…', 'N/A', 'N/A', 0, 0, 0, 2]]
    return render_template('search.html', data=data, hashtag=hashtag)

if __name__ == "__main__":
    app.debug = True
    app.run()
