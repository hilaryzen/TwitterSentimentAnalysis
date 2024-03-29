from flask import Flask, render_template, request
from datetime import datetime, timedelta
import requests
import os
import json
import pandas as pd
import numpy as np
from flair.models import TextClassifier
classifier = TextClassifier.load('en-sentiment')
from flair.data import Sentence
import sqlite3
app = Flask(__name__)

# export 'BEARER_TOKEN'='<your_bearer_token>'
bearer_token = os.environ.get("BEARER_TOKEN")

# Create database
def create_db():
    db = sqlite3.connect("tweets.db")
    cursor = connection.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS tweets (text TEXT, domain_name TEXT, domain_desc TEXT, likes INTEGER, quotes INTEGER, replies INTEGER, retweets INTEGER, score INTEGER, pred TEXT, score_sign INTEGER, search TEXT)")
    db.commit()
    db.close()

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

# Define a function to get Flair sentiment prediction score
def score_flair(text):
    sentence = Sentence(text)
    classifier.predict(sentence)
    score = sentence.labels[0].score
    value = sentence.labels[0].value
    return score, value

def calculate_sentiment(data, col_values, search):
    tweets = pd.DataFrame(data = data, columns = col_values)
    # Add dataframe columns for sentiment analysis results
    tweets['score'] = tweets['text'].apply(lambda s: score_flair(s)[0])
    tweets['pred'] = tweets['text'].apply(lambda s: score_flair(s)[1])
    tweets['score_sign'] = tweets.apply(lambda row: round(row['score'], 2) if row['pred'] == 'POSITIVE' else round(-row['score'], 2), axis=1)
    tweets['search'] = search

    # Add new tweets to SQL db
    db = sqlite3.connect("tweets.db")
    tweets.to_sql('tweets', db, if_exists='append', index=False)
    db.commit()
    db.close()

    freq = tweets['pred'].value_counts()
    return tweets.to_numpy(), round(tweets['score_sign'].mean(), 2), freq['POSITIVE'], freq['NEGATIVE']

@app.route("/", methods=["GET", "POST"])
def home():
    return render_template('home.html')

@app.route("/search", methods=["GET", "POST"])
def search():
    # Get searched hashtag
    hashtag = request.form['hashtag']

    # Query Twitter API with search term
    search_url = "https://api.twitter.com/2/tweets/search/recent"
    start_time = datetime.now() - timedelta(days=1)
    start_time = start_time.isoformat('T', 'seconds') + 'Z'
    query = hashtag.strip() + ' lang:en'
    query_params = {'query': query, 'tweet.fields': 'context_annotations,public_metrics', 'start_time': start_time, 'max_results': 100}
    json_response = connect_to_endpoint(search_url, query_params)

    # Transform tweet data and perform sentiment analysis
    columns, data = convert_tweets_json(json_response)
    tweets_df, score_mean, num_pos, num_neg = calculate_sentiment(data, columns, hashtag)

    return render_template('search.html', data=tweets_df, hashtag=hashtag, avg=score_mean, num_pos=num_pos, num_neg=num_neg)

if __name__ == "__main__":
    app.debug = True
    app.run()
