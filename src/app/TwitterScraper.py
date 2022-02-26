import signal
import os
import sys
import json
import time
from urllib.parse import parse_qs, urlparse
from selenium import webdriver
from requests_futures.sessions import FuturesSession
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import random
import re
from pyvirtualdisplay import Display


class TwitterScraper:
    random_user_no = 0

    def __init__(self, db_connection, enable_chrome_driver, test_env=None):
        if test_env:
            display = Display(visible=0, size=(800, 600))
            display.start()
        self.db_connection = db_connection
        self.enable_chrome_driver = False
        if enable_chrome_driver:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--window-size=1420,1080')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-dev-shm-usage')
            self.enable_chrome_driver = True
            try:
                self.driver = webdriver.Chrome(options=chrome_options)

            except Exception as e:
                print("Error on line {}".format(sys.exc_info()[-1].tb_lineno))
                print("ERROR: " + str(e))
                print("reconnecting to chrome driver")
                time.sleep(60)
                self.driver = webdriver.Chrome(options=chrome_options)
        else:
            self.enable_chrome_driver = False

    def twitter_login(self, username, password):

        try:
            self.driver.get('https://twitter.com/login')
            time.sleep(10)
            text_area1 = self.driver.find_element_by_name('session[username_or_email]')
            text_area1.clear()
            # text_area1.send_keys(account["username"])
            text_area1.send_keys(username)
            text_area = self.driver.find_element_by_name('session[password]')
            text_area.clear()
            # text_area.send_keys(account["password"])
            text_area.send_keys(password)
            # text_area = driver.find_element_by_name('remember_me').click()
            submit_button = self.driver.find_element_by_xpath("//div[@data-testid='LoginForm_Login_Button']")
            submit_button.click()
            time.sleep(5)
        except Exception as e:
            ("error: " + str(e))

    def get_auth_object_from_cookies(self, username, password):
        auth_object = dict()
        auth_object["username"] = username
        print("login with username: ", username)
        auth_object["password"] = password
        auth_object["x-guest-token"] = ""
        auth_object["x-csrf-token"] = ""
        auth_object["auth_token"] = ""
        auth_object["ct0"] = ""
        auth_object["_twitter_sess"] = ""
        cookies = self.driver.get_cookies()
        try:
            auth_object["_twitter_sess"] = next((cookie for cookie in cookies if cookie['name'] == "_twitter_sess"))[
                'value']
            auth_object["ct0"] = next((cookie for cookie in cookies if cookie['name'] == "ct0"))['value']
            auth_object["x-guest-token"] = next((cookie for cookie in cookies if cookie['name'] == "gt"))['value']
            auth_object["x-csrf-token"] = auth_object["ct0"]
            auth_object["auth_token"] = next((cookie for cookie in cookies if cookie['name'] == "auth_token"))['value']
        except:
            auth_object = self.driver.get_cookies()
            auth_object["_twitter_sess"] = next((cookie for cookie in cookies if cookie['name'] == "_twitter_sess"))[
                'value']
            auth_object["auth_token"] = next((cookie for cookie in cookies if cookie['name'] == "auth_token"))['value']
            auth_object["ct0"] = next((cookie for cookie in cookies if cookie['name'] == "ct0"))['value']
            auth_object["x-guest-token"] = next((cookie for cookie in cookies if cookie['name'] == "gt"))['value']
            auth_object["x-csrf-token"] = auth_object["ct0"]
        self.sql_update_twitter_login(auth_object)
        return auth_object

    def find_values(self, id, json_repr):
        results = []

        def _decode_dict(a_dict):
            try:
                results.append(a_dict[id])
            except KeyError:
                print("error: decode dict in find_values()")
                pass
            return a_dict

        json.loads(json_repr, object_hook=_decode_dict)  # Return value ignored.
        return results

    def get_auth_object(self):
        auth_object = dict()
        auth_object["username"] = ""
        auth_object["password"] = ""
        auth_object["x-guest-token"] = ""
        auth_object["x-csrf-token"] = ""
        auth_object["auth_token"] = ""
        auth_object["ct0"] = ""
        auth_object["_twitter_sess"] = ""
        auth_obj_db = self.get_auth_object_from_db()
        auth_object["username"] = auth_obj_db[1]
        auth_object["password"] = auth_obj_db[2]
        auth_object["x-csrf-token"] = auth_obj_db[3]
        auth_object["_twitter_sess"] = auth_obj_db[4]
        auth_object["ct0"] = auth_obj_db[5]
        auth_object["auth_token"] = auth_obj_db[6]
        auth_object["x-guest-token"] = auth_obj_db[7]
        return auth_object

    def prepare_request(self, tweet_id, username, context, auth_object=None):
        if auth_object is None:
            auth_object = self.get_auth_object()
        referrer = "retweets" if context == "retweeted_by" else "likes"
        headers = {
            'authority': 'twitter.com',
            'sec-ch-ua': '"Chromium";v="86", "\\"Not\\\\A;Brand";v="99", "Google Chrome";v="86"',
            'x-twitter-client-language': 'en',
            'x-csrf-token': auth_object['x-csrf-token'],
            'sec-ch-ua-mobile': '?0',
            'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.80 Safari/537.36',
            'x-twitter-auth-type': 'OAuth2Session',
            'x-twitter-active-user': 'yes',
            'accept': '*/*',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://twitter.com/{}/status/{}/{}'.format(username, tweet_id, referrer),
            'accept-language': 'en-US,en;q=0.9',
            'cookie': 'gt={}; ct0={}; _twitter_sess={}; auth_token={}'.format(auth_object["x-guest-token"],
                                                                              auth_object["ct0"],
                                                                              auth_object["_twitter_sess"],
                                                                              auth_object["auth_token"].replace(";",
                                                                                                                "")),
        }

        params = (
            ('include_profile_interstitial_type', '1'),
            ('include_blocking', '1'),
            ('include_blocked_by', '1'),
            ('include_followed_by', '1'),
            ('include_want_retweets', '1'),
            ('include_mute_edge', '1'),
            ('include_can_dm', '1'),
            ('include_can_media_tag', '1'),
            ('skip_status', '1'),
            ('cards_platform', 'Web-12'),
            ('include_cards', '1'),
            ('include_ext_alt_text', 'true'),
            ('include_quote_count', 'true'),
            ('include_reply_count', '1'),
            ('tweet_mode', 'extended'),
            ('include_entities', 'true'),
            ('include_user_entities', 'true'),
            ('include_ext_media_color', 'true'),
            ('include_ext_media_availability', 'true'),
            ('send_error_codes', 'true'),
            ('simple_quoted_tweet', 'true'),
            ('tweet_id', tweet_id),
            ('ext', 'mediaStats,highlightedLabel'),
        )

        url = 'https://twitter.com/i/api/2/timeline/{}.json'.format(context)
        return url, headers, params

    def send_retweet_like_requests(self, interactions_request_list, context):
        results = []
        tweet_users_list = []
        with FuturesSession() as session:
            futures = [session.get(endpoint["url"], headers=endpoint["headers"], params=endpoint["params"]) for endpoint
                       in interactions_request_list]
            for future in futures:
                if future.result().status_code == 200:
                    parsed = urlparse(future.result().request.url)
                    tweet_id = parse_qs(parsed.query)['tweet_id']
                    results.append([json.loads(future.result().content), tweet_id[0]])
                else:
                    print("Response status code {}. Response from twitter {} ".format(future.result().status_code,
                                                                                      future.result().content))
        for result in results:
            users = result[0]["globalObjects"]["users"]
            tweet = dict()
            usernames = []
            for key in users:
                user = dict()
                user["username"] = users[key]["screen_name"]
                usernames.append(user)
            if len(usernames) > 0:
                value = [context, usernames]
                tweet[result[1]] = value
                tweet_users_list.append(tweet)
        return tweet_users_list

    def get_auth_object_from_db(self):
        twitter_logins = self.sql_twitter_logins_fetch()
        twitter_auth_obj = None
        if len(twitter_logins) > 1:
            self.random_user_no = random.randrange(0, len(twitter_logins))
            twitter_auth_obj = twitter_logins[self.random_user_no]
        if len(twitter_logins) == 1:
            twitter_auth_obj = twitter_logins[0]
        return twitter_auth_obj

    def get_tweets_users(self, tweets, context):
        interactions_request_list = []
        if not self.enable_chrome_driver:
            for tweet in tweets:
                url, headers, params = self.prepare_request(tweet["id"], tweet["username"], context)
                interaction_request = dict()
                interaction_request["url"] = url
                interaction_request["headers"] = headers
                interaction_request["params"] = params
                interactions_request_list.append(interaction_request)
        else:
            auth_obj_db = self.get_auth_object_from_db()
            self.twitter_login(auth_obj_db[1], auth_obj_db[2])
            auth_obj = self.get_auth_object_from_cookies(auth_obj_db[1], auth_obj_db[2])
            for tweet in tweets:
                url, headers, params = self.prepare_request(tweet["id"], tweet["username"], context, auth_obj)
                interaction_request = dict()
                interaction_request["url"] = url
                interaction_request["headers"] = headers
                interaction_request["params"] = params
                interactions_request_list.append(interaction_request)
        return self.send_retweet_like_requests(interactions_request_list, context)

    def sql_twitter_logins_fetch(self):
        con = self.db_connection
        cursor_obj = con.cursor()
        cursor_obj.execute('SELECT * FROM twitterlogin')
        rows = cursor_obj.fetchall()
        return rows

    def sanitize_data(self, data):
        if data is not None:
            return str(re.sub(r"[\"\';\n]", "", data))

        return ""

    def sql_update_twitter_login(self, auth_object):
        con = self.db_connection
        cursor_obj = con.cursor()
        query_string = """UPDATE twitterlogin SET xcsrftoken = ?, twittersession = ?, ct0 = ?, authtoken = ?,
                                guestoken = ?  where username = ? """

        x_csrf_token = self.sanitize_data(auth_object["x-csrf-token"])
        twitter_sess = self.sanitize_data(auth_object["_twitter_sess"])
        ct0 = self.sanitize_data(auth_object["ct0"])
        auth_token = self.sanitize_data(auth_object["auth_token"])
        x_guest_token = self.sanitize_data(auth_object["x-guest-token"])
        username = self.sanitize_data(auth_object["username"])

        cursor_obj.execute(query_string, (x_csrf_token, twitter_sess,
                                          ct0, auth_token,
                                          x_guest_token, username,))
        con.commit()

    def find_values(self, id, json_repr):
        results = []

        def _decode_dict(a_dict):
            if id in a_dict:
                results.append(a_dict[id])
                return a_dict

        json.loads(json_repr, object_hook=_decode_dict)  # Return value ignored.
        return results

    def quit_driver_and_pickup_children(self):
        self.driver.quit()
        try:
            pid = True
            while pid:
                pid = os.waitpid(-1, os.WNOHANG)
                try:
                    if pid[0] == 0:
                        pid = False
                except Exception as e:
                    print(str(e))
                    pass

        except Exception as e:
            print(str(e))
            pass

    def kill_process(self):
        try:
            # iterating through each instance of the process
            for line in os.popen("ps -eo pid,etime,command | grep chrome | grep -v grep | awk '{print $1, $2, $3}'"):
                fields = line.split()
                # extracting Process ID from the output
                pid = fields[0]
                # terminating process
                if len(fields[1].split(":")) > 2:
                    os.kill(int(pid), signal.SIGKILL)
                    print("Process Successfully terminated")
        except Exception as e:
            print("Error on line {}".format(sys.exc_info()[-1].tb_lineno))
            print("kill_process ERROR: " + str(e))

    def tearDown(self):
        if self.enable_chrome_driver:
            if self.driver is None:
                return
            self.quit_driver_and_pickup_children()
            self.kill_process()
