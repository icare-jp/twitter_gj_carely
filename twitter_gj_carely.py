import sys
sys.dont_write_bytecode = True
import requests
import os
import json
from requests_oauthlib import OAuth1Session
import time
import traceback
import tweepy
from dotenv import load_dotenv
load_dotenv()
import psycopg2
import random
import datetime
from pytz import timezone
import users_dictionary

# テストアカウント
# consumer_key = os.environ.get("TEST_CONSUMER_KEY")
# consumer_secret = os.environ.get("TEST_CONSUMER_SECRET")
# access_token = os.environ.get("TEST_ACCESS_TOKEN")
# access_token_secret = os.environ.get("TEST_ACCESS_TOKEN_SECRET")
# bearer_token = os.environ.get("TEST_BEARER_TOKEN")

# 公式アカウント
consumer_key = os.environ.get("CONSUMER_KEY")
consumer_secret = os.environ.get("CONSUMER_SECRET")
access_token = os.environ.get("ACCESS_TOKEN")
access_token_secret = os.environ.get("ACCESS_TOKEN_SECRET")
bearer_token = os.environ.get("BEARER_TOKEN")

# 本番DB
host = os.environ.get("HOST")
port = os.environ.get("PORT")
dname = os.environ.get("DNAME")
user = os.environ.get("DBUSER")
password = os.environ.get("PASSWORD")

Bot_twitter_id = "GJ_Carely" # Botの@なしのTwitterID 本番が"GJ_Carely" テストが"GJCarely_test"

# API V1.1
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
API = tweepy.API(auth)
# API V2.0
Client = tweepy.Client(bearer_token, consumer_key, consumer_secret, access_token, access_token_secret)

def bearer_oauth(r):
    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2FilteredStreamPython"
    return r

def get_rules():
    print("1.get_rulesを実行")
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream/rules", auth=bearer_oauth
    )
    if response.status_code != 200:
        raise Exception(
            "get_rulesで失敗（HTTP {}）: {}".format(response.status_code, response.text)
        )
    print(json.dumps(response.json()))
    return response.json()

def delete_all_rules(rules):
    print("2.dlete_all_rulesを実行")
    if rules is None or "data" not in rules:
        return None

    ids = list(map(lambda rule: rule["id"], rules["data"]))
    payload = {"delete": {"ids": ids}}
    response = requests.post(
        "https://api.twitter.com/2/tweets/search/stream/rules",
        auth=bearer_oauth,
        json=payload
    )
    if response.status_code != 200:
        raise Exception(
            "delete_rulesで失敗（HTTP {}）: {}".format(
                response.status_code, response.text
            )
        )
    print(json.dumps(response.json()))
    return response.json()

def set_rules(delete):
    print("3.set_rulesを実行")
    rules = [
        {
            "value":f'@{Bot_twitter_id} - from:{Bot_twitter_id}'
        }
    ]
    payload = {"add": rules}
    response = requests.post(
        "https://api.twitter.com/2/tweets/search/stream/rules",
        auth=bearer_oauth,
        json=payload,
    )
    if response.status_code != 201:
        raise Exception(
            "set_rulesで失敗（HTTP {}）: {}".format(response.status_code, response.text)
        )
    print(json.dumps(response.json()))
    return response.json()

def get_stream(headers):
    print("4.get_streamを実行")
    run = 1
    while run:
        try:
            with requests.get(
                "https://api.twitter.com/2/tweets/search/stream", auth=bearer_oauth, stream=True,
            ) as response:
                print(response.status_code)
                if response.status_code == 429:
                    raise ConnectionError(
                        "429で例外を発生"
                    )
                elif response.status_code != 200:
                    raise Exception(
                        "get_streamで失敗（HTTP {}）: {}".format(
                            response.status_code, response.text
                        )
                    )
                run=1
                for response_line in response.iter_lines():
                    if response_line:
                        reply(response_line)

        except ChunkedEncodingError as chunkError:
            print(traceback.format_exc())
            time.sleep(10)
            continue
        except ConnectionResetError as e:
            print("ConnectionResetErrorで例外キャッチ")
            print(e)
            run+=1
            if run < 15:
                print(f'再接続します{run-1}回目：{2**run}秒sleep')
                time.sleep(2**run)
                continue
            else:
                run=0
        except ConnectionError as e:
            print("ConnectionErrorで例外キャッチ")
            print(e)
            run+=1
            if run < 15:
                print(f'再接続します{run-1}回目：{2**run}秒sleep')
                time.sleep(2**run)
                continue
            else:
                run=0
        except Exception as e:
            print("事前に把握していないエラーが発生したので5分待機して再接続を試みます")
            print(e)
            run+=1
            if run < 15:
                print(f'再接続します{run-1}回目：{2**run}秒sleep')
                time.sleep(2**run)
                continue
            else:
                run=0
    return response.json()

class ChunkedEncodingError(Exception):
    pass

def get_points(name):
    conn = psycopg2.connect(host=host, port=port, dbname=dname, user=user, password=password)
    cur = conn.cursor()

    # twitterアカウント名からslackのuser_idを取得
    user_id = users_dictionary.get_user_id(name)

    # メンションされたアカウント名のslack_idが存在すれば
    if user_id:
        # 指定したidのポイントを取得
        cur.execute(f'SELECT rc.appreciation_count, rc.appreciation_date FROM receiver_counts rc WHERE rc.user_id={user_id} ORDER BY rc.created_at DESC LIMIT 1')
        (appreciation_count, appreciation_date) = cur.fetchone()

        if appreciation_date == datetime.date.today():
            # 1ポイント加算してレコードを更新
            appreciation_count += 1
            cur.execute(f"UPDATE receiver_counts SET appreciation_count={appreciation_count} WHERE user_id={user_id} and appreciation_date=date'{datetime.date.today()}'")
        else:
            # 1ポイントでレコードを新規作成
            appreciation_count = 1
            cur.execute(f"INSERT INTO receiver_counts(appreciation_date, appreciation_count, created_at, updated_at, user_id) VALUES (date'{datetime.date.today()}', {appreciation_count}, timestamp'{datetime.datetime.now()}', timestamp'{datetime.datetime.now()}', {user_id})")

        conn.commit()
        cur.close()
        conn.close()
    else:
        appreciation_count = 0
    return appreciation_count

def reply(response_line):
    json_response = json.loads(response_line)
    tweet_id = int(json_response["data"]["id"])
    received_text = json_response["data"]["text"]
    names = [name for name in received_text.split() if name.startswith('@') and name != f'@{Bot_twitter_id}']
    combined_names = 'と'.join(names)
    reply_text = f'😎ヘイ、みんな！{combined_names} がほめられたよ！🤟' # Botが返信するテキスト

    is_5_points = False
    is_10_points = False
    is_20_points = False
    for name in names:
        point = get_points(name)
        if point:
            reply_text += f'\n{name} は {point} ポイント目をゲッツ！🎉🎉🎉'
            if point == 5:
                is_5_points = True
            elif point == 10:
                is_10_points = True
            elif point == 20:
                is_20_points = True
        else:
            reply_text += f'\n{name} は新たにポイントをゲッツ！🎉🎉🎉'

    # 5 or 10 or 20ポイントであればgif画像を添付
    filename = ''
    if is_5_points:
        filename = 'point_5.gif'
    elif is_10_points:
        filename = 'point_10.gif'
    elif is_20_points:
        filename = 'point_20.gif'

    # メンションが多すぎて140文字を超えてしまった場合
    if len(reply_text) > 140:
        reply_text = '140文字を超えてしまってGJできないぞ😎\nメンションを分けてくれ！'
        filename = ''
    else:
        # gjした人のポイント加算処理
        author_name = '@' + str(Client.get_tweet(id=tweet_id, expansions="author_id", user_fields=["username"]).includes["users"][0])
        increment_giver_count(author_name)

    print(reply_text)

    if filename:
        API.update_status_with_media(filename=filename, status=reply_text, in_reply_to_status_id=tweet_id, auto_populate_reply_metadata=True)
    else:
        API.update_status(status=reply_text, in_reply_to_status_id=tweet_id, auto_populate_reply_metadata=True)

def increment_giver_count(author_name):
    conn = psycopg2.connect(host=host, port=port, dbname=dname, user=user, password=password)
    cur = conn.cursor()

    # twitterアカウント名からslackのuser_idを取得
    user_id = users_dictionary.get_user_id(author_name)

    # メンションされたアカウント名のslack_idが存在すれば
    if user_id:
        # 指定したidのポイントを取得
        cur.execute(f'SELECT rc.appreciation_count, rc.appreciation_date FROM giver_counts rc WHERE rc.user_id={user_id} ORDER BY rc.created_at DESC LIMIT 1')
        (appreciation_count, appreciation_date) = cur.fetchone()

        if appreciation_date == datetime.date.today():
            # 1ポイント加算してレコードを更新
            appreciation_count += 1
            cur.execute(f"UPDATE giver_counts SET appreciation_count={appreciation_count} WHERE user_id={user_id} and appreciation_date=date'{datetime.date.today()}'")
        else:
            # 1ポイントでレコードを新規作成
            appreciation_count = 1
            cur.execute(f"INSERT INTO giver_counts(appreciation_date, appreciation_count, created_at, updated_at, user_id) VALUES (date'{datetime.date.today()}', {appreciation_count}, timestamp'{datetime.datetime.now()}', timestamp'{datetime.datetime.now()}', {user_id})")

        conn.commit()
        cur.close()
        conn.close()
    else:
        appreciation_count = 0
    return appreciation_count

def main():
    rules = get_rules()
    delete = delete_all_rules(rules)
    set = set_rules(delete)
    get_stream(set)

main()
