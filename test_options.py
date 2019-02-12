# coding: UTF-8
import json
import os
import requests
import datetime
from time import sleep
import sys


USERLIST_URL = "https://slack.com/api/users.list"
USER_ACCESS_LOG_URL = "https://slack.com/api/team.accessLogs"
DELETE_URL = "https://slack.com/api/users.admin.setInactive"
LAST_UPDATE_DATE = 180
USER_LIST_TOKEN = sys.argv[1]
USER_ACCESSLOG_TOKEN = sys.argv[2]


def get_userinfo():
    key = USER_LIST_TOKEN
    payload = {"token": key}
    r = requests.get(USERLIST_URL, params=payload)
    return r.json()


def get_user_access_logs(before):
    key = USER_ACCESSLOG_TOKEN
    payload = {"token": key, "count": 1000, "before": before}
    r = requests.get(USER_ACCESS_LOG_URL, params=payload)
    return r.json()


def get_unixtime_now():
    now = datetime.datetime.now()
    return int(now.timestamp())


def get_unixtime_before():
    now = datetime.datetime.now()
    delta_time = now - datetime.timedelta(days=LAST_UPDATE_DATE)
    return int(delta_time.timestamp())


def get_users_from_access_log(before):
    d = {}
    before_time = get_unixtime_before()
    user_access_logs = get_user_access_logs(before)
    users = user_access_logs.get("logins")
    if users:
        for user in users:
            if user["date_last"] > before_time:
                date_time = convert_date_time(user["date_last"])
                d[user["user_id"]] = {user["username"]: date_time}
        d["date_last"] = users[-1]["date_last"]
    return d


def get_access_users():
    d = {}
    i = 0
    now = get_unixtime_now()
    before_time = get_unixtime_before()
    user_data = get_users_from_access_log(now)
    if user_data.get("date_last"):
        while user_data.get("date_last") > before_time:
            # 20+ per minuteで制限に引っかかるので1分待つ
            # https://api.slack.com/docs/rate-limits
            i = i + 1
            if i % 20 == 0:
                sleep(60)
            d.update(user_data)
            user_data = get_users_from_access_log(user_data.get("date_last"))
    return d


def convert_date_time(unix_time):
    date_time = datetime.datetime.fromtimestamp(unix_time)
    return date_time.strftime("%Y-%m-%d %H:%M:%S")


def get_guest_users():
    d = {}
    user_info = get_userinfo()
    user_list = user_info["members"]
    for user in user_list:
        if user.get("deleted") is False and user.get("is_restricted") is True:
            d[user["id"]] = user["name"]
    return d


def get_inactive_guests():
    d = {}
    guest_users = get_guest_users()
    access_users = get_access_users()
    for k, v in guest_users.items():
        if not access_users.get(k):
            d[k] = v
    return d


def del_slack_user(user_id):
    key = USER_LIST_TOKEN
    payload = {"token": key, "user": user_id}
    r = requests.delete(DELETE_URL, params=payload)
    return r.json()


# ユーザー削除
def del_disuse_slack_guestusers():
    inactive_guests = get_inactive_guests()
    for k, v in inactive_guests.items():
        print(k, v)
        r = del_slack_user(k)
        print(r)


print(USER_LIST_TOKEN)
print(USER_ACCESSLOG_TOKEN)
a = get_userinfo()
print(a)
r = get_inactive_guests()
print(r)
