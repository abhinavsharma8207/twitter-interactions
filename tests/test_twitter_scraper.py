from __future__ import absolute_import, division, print_function
import unittest
import sqlite3
import os, time
import json
import re

RABBITMQ_USER = os.environ['RABBITMQ_USER'] = 'guest'
RABBITMQ_PASSWORD = os.environ['RABBITMQ_PASSWORD'] = 'guest'
RABBITMQ_HOST = os.environ['RABBITMQ_HOST'] = 'localhost'
enable_chrome_driver = os.environ['ENABLE_CHROME_DRIVER'] = 'True'

from selenium import webdriver
# local import
# import the package
import app
from app.TwitterScraper import TwitterScraper

class TestTwitterScraper(unittest.TestCase):


    def get_db_connection(self):
        try:
            db_connection = sqlite3.connect("/data/tests/data/twitterlogin.db")
            return db_connection
        except Error:
            print("Unit Test - get_db_connection: ", Error)

    def test_selenium_driver_working(self):
        scraper = TwitterScraper(self.get_db_connection(), True)
        assert scraper.driver is not None

    def test_get_auth_object_from_db(self):
        scraper = TwitterScraper(self.get_db_connection(), True)
        auth_object_db = scraper.get_auth_object_from_db()
        assert not not auth_object_db[0]
        assert not not auth_object_db[1]

    def test_instagram_login(self):
        scraper = TwitterScraper(self.get_db_connection(), True)
        auth_object_db = scraper.get_auth_object_from_db()
        scraper.twitter_login(auth_object_db[1], auth_object_db[2])
        scraper.driver.get_cookies()
        driver_url = scraper.driver.current_url
        assert not not driver_url

    
    def test_get_auth_object_from_cookies(self):
        scraper = TwitterScraper(self.get_db_connection(), True)
        scraper.sql_twitter_logins_fetch()
        auth_object_db = scraper.get_auth_object_from_db()
        testing_username = auth_object_db[1]
        scraper.twitter_login(auth_object_db[1], auth_object_db[2])
        scraper.driver.get_cookies()
        auth_object = scraper.get_auth_object_from_cookies(auth_object_db[1], auth_object_db[2])
        scraper.sql_update_twitter_login(auth_object)
        scraper.tearDown()
        assert not not auth_object["username"]
        assert not not auth_object["password"]
        assert not not auth_object["x-guest-token"]
        assert not not auth_object["x-csrf-token"]
        assert not not auth_object["auth_token"]
        assert not not auth_object["ct0"]
        assert not not auth_object["_twitter_sess"]


    def test_send_retweet_like_requests(self):
        context = "retweeted_by"
        interactions_request_list = []
        scraper = TwitterScraper(self.get_db_connection(), True)
        scraper.sql_twitter_logins_fetch()
        auth_object_db = scraper.get_auth_object_from_db()
        testing_username = auth_object_db[1]
        scraper.twitter_login(auth_object_db[1], auth_object_db[2])
        scraper.driver.get_cookies()
        with open('tests/data/tweet.json', 'r', encoding='utf-8') as json_file:
            tweets = json.load(json_file)
            for tweet in tweets:
                url, headers, params = scraper.prepare_request(tweet["id"], tweet["username"], context)
                interaction_request = dict()
                interaction_request["url"] = url
                interaction_request["headers"] = headers
                interaction_request["params"] = params
                interactions_request_list.append(interaction_request)

                tweet_users_list = scraper.send_retweet_like_requests(interactions_request_list, context)
                assert not not tweet_users_list
                


    def test_get_users_interaction_metrics(self):
        scraper = TwitterScraper(self.get_db_connection(), True)
        scraper.sql_twitter_logins_fetch()
        auth_object_db = scraper.get_auth_object_from_db()
        scraper.twitter_login(auth_object_db[1], auth_object_db[2])
        scraper.driver.get_cookies()
        auth_object = scraper.get_auth_object_from_cookies(auth_object_db[1], auth_object_db[2])
        scraper.sql_update_twitter_login(auth_object)
        with open('tests/data/tweet.json', 'r', encoding='utf-8') as json_file:
            tweet = json.load(json_file)
            tweet_users_likes = scraper.get_tweets_users(tweet, "liked_by")

            self.assertIsNotNone(tweet_users_likes)


    def init_scraper(self):
        scraper = TwitterScraper(self.get_db_connection(), True)
        scraper.sql_twitter_logins_fetch()
        auth_object_db = scraper.get_auth_object_from_db()
        scraper.twitter_login(auth_object_db[1], auth_object_db[2])

        return scraper, auth_object_db

    def sql_twitter_logins_fetch_by_username(self, param):
        try:
            con = self.get_db_connection()
            cursor_obj = con.cursor()
            cursor_obj.execute('SELECT * FROM twitterlogin WHERE username = ?', (param,))
            rows = cursor_obj.fetchall()
            return rows
        except Exception as e:
            print("Error in getting from db" + str(e))


    @classmethod
    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
