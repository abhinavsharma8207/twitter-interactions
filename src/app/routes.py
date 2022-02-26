import os
import sys
from threading import Thread
import time
import pika
from flask import request
from app import app
import json
from .TwitterScraper import TwitterScraper
from tenacity import retry, stop_after_attempt
from collections import defaultdict
from functools import reduce
import sqlite3
from sqlite3 import Error


def getPassword():
    if 'RABBITMQ_PASSWORD' in os.environ:
        return os.environ['RABBITMQ_PASSWORD']
    else:
        sys.exit('Missing environment variable RABBITMQ_PASSWORD')
        return None
    return None


RABBITMQ_USER = None
RABBITMQ_PASSWORD = getPassword()
RABBITMQ_HOST = None
CHUNK_SIZE = 50
DB_PATH = '/app/database/'
ENABLE_CHROME_DRIVER = True

if 'ENABLE_CHROME_DRIVER' in os.environ:
    ENABLE_CHROME_DRIVER = os.environ['ENABLE_CHROME_DRIVER']

if 'RABBITMQ_USER' in os.environ:
    RABBITMQ_USER = os.environ['RABBITMQ_USER']
else:
    sys.exit('Missing environment variable RABBITMQ_USER')

if 'RABBITMQ_HOST' in os.environ:
    RABBITMQ_HOST = os.environ['RABBITMQ_HOST']
else:
    sys.exit('Missing environment variable RABBITMQ_HOST')


def get_db_path():
    return DB_PATH + 'twitterlogin.db'


def init_sql_connection():
    try:
        con = sqlite3.connect(get_db_path())
        return con
    except Error:
        print(Error)


def init_connection(queue_name=""):
    # global connection
    # global channel
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST, port=5672, virtual_host='/', credentials=credentials,
                                      heartbeat=600, blocked_connection_timeout=300))

    except Exception as e:
        print(" ERROR initialising connection: " + str(e))
    else:
        channel = connection.channel()
        if queue_name:
            channel.queue_declare(queue=queue_name, durable=True)  # Declare a queue
            channel.exchange_declare(exchange='tora', exchange_type='direct', durable=True)
            channel.queue_bind(exchange='tora',
                               queue=queue_name,
                               routing_key=queue_name)
        else:
            channel.exchange_declare(exchange='tora', exchange_type='direct', durable=True)

    return connection


def close_connection(connection):
    # global connection
    # global channel
    if connection is None:
        return
    if not connection.is_open:
        return
    connection.close()


def close_db_connection(connection):
    if connection is None:
        return
    connection.close()


@retry(reraise=True, stop=stop_after_attempt(3))
def publish(doc, queue, connection):
    #    print("doing publish " + queue)
    if connection is None or not connection.is_open:
        print(" WARNING in publish(): connection doesn't exist, opening it ...")
        connection = init_connection(queue)

    channel = connection.channel()
    try:
        channel.basic_publish(exchange='tora',
                              routing_key=queue,
                              body=doc,
                              properties=pika.BasicProperties(delivery_mode=2))
    except Exception as e:
        print(" ERROR while publishing document: " + str(e))


@app.route('/retweets_likes', methods=['POST'])
def retweets_likes():
    tweets = request.get_json()
    if tweets is not None:
        t = Thread(target=get_retweets_likes, args=(tweets,))
        t.start()
    return ('', 200)


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def merge_dictionary(r, d):
    for k in d:
        r[k].append(d[k])


def get_retweets_likes(tweets, test_env=None):
    connection = init_connection()
    db_connection = init_sql_connection()
    t_s = time.time()
    try:
        response_list = []
        if test_env is not None:
            bot = TwitterScraper(db_connection, ENABLE_CHROME_DRIVER, test_env)
        else:
            bot = TwitterScraper(db_connection, ENABLE_CHROME_DRIVER)
        if len(tweets) > 0:
            sub_lists = chunks(tweets, CHUNK_SIZE)
            for sub_list in sub_lists:
                retweeters = bot.get_tweets_users(sub_list, "retweeted_by")
                favoriters = bot.get_tweets_users(sub_list, "liked_by")
                retweeters_favoriters = retweeters + favoriters
                retweeters_favoriters_merged_list = reduce(lambda r, d: merge_dictionary(r, d) or r,
                                                           retweeters_favoriters,
                                                           defaultdict(list))
                for tweet_key in retweeters_favoriters_merged_list:
                    retweeted_by = []
                    liked_by = []

                    if len(retweeters_favoriters_merged_list[tweet_key]) > 1:
                        retweeted_by = retweeters_favoriters_merged_list[tweet_key][0][1]
                        liked_by = retweeters_favoriters_merged_list[tweet_key][1][1]
                    else:
                        if retweeters_favoriters_merged_list[tweet_key][0][0] == "retweeted_by":
                            retweeted_by = retweeters_favoriters_merged_list[tweet_key][0][1]
                            liked_by = []
                        else:
                            retweeters_favoriters_merged_list[tweet_key][0][0]
                            retweeted_by = []
                            liked_by = retweeters_favoriters_merged_list[tweet_key][0][1]
                    n = len(retweeted_by)
                    n += len(liked_by)
                    if n == 0:
                        continue
                    out_json = json.dumps({
                        'id': tweet_key,
                        'retweeted_by': retweeted_by,
                        'liked_by': liked_by
                    })
                    try:
                        publish(out_json, 'interactions', connection)
                        response_list.append(out_json)
                    except Exception as e:
                        print("Exception in get_retweets_likes() while publishing: " + str(e))
                        continue

            return response_list
            print("\n Total time for getting retweets/likes of %d tweets: %.3f s" % (len(tweets), time.time() - t_s))
            print(" Average time per tweet: %f s" % ((time.time() - t_s) / len(tweets)))

    except Exception as e:
        print("Error on line {}".format(sys.exc_info()[-1].tb_lineno))
        print("ERROR: " + str(e))

    finally:
        if bot is not None:
            bot.tearDown()
        close_db_connection(db_connection)
        close_connection(connection)
