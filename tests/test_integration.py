# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
import os, shutil, time

RABBITMQ_USER = os.environ['RABBITMQ_USER'] = 'guest'
RABBITMQ_PASSWORD= os.environ['RABBITMQ_PASSWORD'] = 'guest'
RABBITMQ_HOST= os.environ['RABBITMQ_HOST'] = 'localhost'
enable_chrome_driver=os.environ['ENABLE_CHROME_DRIVER'] = 'True'

import json
import subprocess
import time, sqlite3

# local import
# import the package
import app
from app import routes
from app.routes import get_retweets_likes, init_connection, init_sql_connection, close_connection
from app.TwitterScraper import TwitterScraper
import app.routes as module
import unittest


query_rabbitmq="docker ps | grep docker.g42.ae/docker-dmi/docker-hub/rabbitmq:3-management"
start_rabbitmq_image="docker run -d -p 5672:5672 docker.g42.ae/docker-dmi/docker-hub/rabbitmq:3-management"

DB_PATH = '/data/tests/data/'

class TestTweet(unittest.TestCase):


    def test_twitter_scraper(self):
        # Start Test Containers
        start_rabbitmq = ""
        try:
            check_rabbitmq = subprocess.check_output(query_rabbitmq, shell=True)
        except (subprocess.CalledProcessError):
            start_rabbitmq = subprocess.check_output(start_rabbitmq_image, shell=True)
            pass
        time.sleep(30)

        module.DB_PATH = DB_PATH

        # Getting tweet interaction
        with open('tests/data/tweet.json', 'r', encoding='utf-8') as json_file:
            tweets = json.load(json_file)
            response_list = get_retweets_likes(tweets)
            publish_json = response_list[0]

            self.assertIsNotNone(publish_json)
            response_dict = json.loads(publish_json)
            print("response_dict: ", response_dict)
            assert not not response_dict["retweeted_by"]
            assert not not response_dict["liked_by"]

        # Stop Test Containers
        if start_rabbitmq != "":
            killCall = subprocess.Popen('docker stop %s' % start_rabbitmq.decode("utf-8"), shell=True)
        else:
            if check_rabbitmq.decode("utf-8") != "":
                process_rabbitmq = check_rabbitmq.decode("utf-8").split(" ")[000]
                killCall = subprocess.Popen('docker stop %s' % process_rabbitmq, shell=True)

        killCall.wait()


    @classmethod
    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
