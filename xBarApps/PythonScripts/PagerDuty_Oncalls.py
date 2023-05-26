#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# <bitbar.title>PagerDuty Oncalls</bitbar.title>
# <bitbar.version>v0.1</bitbar.version>
# <bitbar.author>Joshua Briefman</bitbar.author>
# <bitbar.author.github>sirgatez</bitbar.author.github>
# <bitbar.desc>Widget PagerDuty oncalls.</bitbar.desc>
# <bitbar.dependencies>bash/zsh and Python 3</bitbar.dependencies>
# <bitbar.image>N/A</bitbar.image>
# <bitbar.abouturl>https://github.com/sirgatez/PagerDuty_Oncalls_xBar</bitbar.abouturl>

import json
import os
import pprint
import requests
import pytz
from pytz import timezone
from datetime import datetime
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Pretty Printer for debugging
pp = pprint.PrettyPrinter(indent=4)

# Configure default retry count on error.
rs = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
rs.mount("https://", HTTPAdapter(max_retries=retries))

APP = os.path.basename(__file__).split(".")[0]
ROOT = "/".join([os.path.dirname(os.path.abspath(__file__)), "config"])


def load_last_pagerduty_reply(filename):
    with open(filename, 'r') as file_handle:
        json_data = "".join(file_handle.readlines())
    return json.loads(json_data)


def save_last_pagerduty_reply(filename, json_data):
    with open(filename, "w") as file_handle:
        json.dump(json_data, file_handle, ensure_ascii=False)


def get_local_time_from_utc(utctime, date_format, time_zone):
    utc_dt = pytz.utc.localize(utctime)
    pst_tz = timezone(time_zone)
    pst_dt = pst_tz.normalize(utc_dt.astimezone(pst_tz))
    return pst_dt.strftime(date_format)


def fetch_pagerduty_team_schedule(dev_token, schedule_ids):
    schedule_req = "limit=100&"
    for schedule_id in schedule_ids:
        schedule_req = "{0}schedule_ids[]={1}&".format(schedule_req, schedule_id)
    schedule_req = schedule_req[:-1]
    return requests.get("https://api.pagerduty.com/oncalls"
                        "?{0}".format(schedule_req),
                        headers={"Accept": "application/vnd.pagerduty+json;version=2",
                                 "Authorization": "Token token={0}".format(dev_token),
                                 "Content-Type": "application/json"})


def get_oncall_from_json(json_data, local_time_fmt, local_time_zone):
    response = dict()
    pagerduty_format = "%Y-%m-%dT%H:%M:%SZ"  # PagerDuty time format

    for schedule in json_data.json()['oncalls']:
        if schedule['escalation_level'] == 2:
            utc_raw_start = datetime.strptime(schedule["start"], pagerduty_format)
            utc_raw_end = datetime.strptime(schedule["end"], pagerduty_format)
            response[schedule['schedule']['id']] = {
                'team': schedule['schedule']['summary'],
                'oncall': schedule['user']['summary'],
                'oncall_url': schedule['user']['html_url'],
                "utc_fmt_start": "{0}UTC".format(
                    datetime.strptime(schedule["start"], pagerduty_format).strftime(local_time_fmt)),
                "utc_fmt_end": "{0}UTC".format(
                    datetime.strptime(schedule["end"], pagerduty_format).strftime(local_time_fmt)),
                "local_fmt_start": get_local_time_from_utc(utc_raw_start, local_time_fmt, local_time_zone),
                "local_fmt_end": get_local_time_from_utc(utc_raw_end, local_time_fmt, local_time_zone)
            }
    return response


def print_xbar_oncalls(oncall_response, pd_company):
    for schedule in oncall_response:
        schedule_url = "https://{0}.pagerduty.com/schedules/{1}".format(pd_company, schedule)
        print("{0} | color='{1}' href='{2}'".format(oncall_response[schedule]['team'], colors['menu'], schedule_url))
        print("-- {0} | color='{1}' href='{2}'".format(
            oncall_response[schedule]['oncall'], colors['menu'], oncall_response[schedule]['oncall_url']))
        print("-- Start: {0} | color='{1}'".format(oncall_response[schedule]['utc_fmt_start'], colors['info']))
        print("-- End: {0} | color='{1}'".format(oncall_response[schedule]['utc_fmt_end'], colors['info']))


# Define colors globally for easy access.
colors = {"menu": "#666666", "info": "#00CC00"}

if __name__ == '__main__':
    stale_data = False
    pagerduty_json = ""
    pagerduty_json_last = ""
    pagerduty_reply = ""
    error_msg = ""
    pagerduty_last_reply_file = "{0}.lastreply".format(APP)  # Stored in same folder as script

    ################################
    ### Begin User Configuration ###
    ################################

    # Authentication and User Config
    PAGER_DUTY_COMPANY = "MyCompany"  # mycompany.pagerduty.com
    PAGER_DUTY_TOKEN = "MyDevToken"  # Configure to your Dev Token
    PAGER_DUTY_SCHEDULES = [
        "ScheduleA",  # TeamA's Schedule
        "ScheduleB",  # TeamB's Schedule
        "ScheduleC",  # TeamC's Schedule
        "ScheduleD",  # TeamD's Schedule
    ]  # Configure to your Team Schedule IDs.

    # Data formatting
    # PAGER_DUTY_DATE_FORMAT = "%m/%d/%Y %H:%M:%S %Z"  # Local military time format
    PAGER_DUTY_DATE_FORMAT = "%m/%d/%Y %I:%M:%S%p %Z"  # Local standard time format
    PAGER_DUTY_TIMEZONE = "US/Pacific"

    ##############################
    ### End User Configuration ###
    ##############################

    try:
        pagerduty_reply = fetch_pagerduty_team_schedule(PAGER_DUTY_TOKEN, PAGER_DUTY_SCHEDULES)
        status_code = pagerduty_reply.status_code
        code = str(pagerduty_reply.status_code)[0:1]
        if code == '2':
            pagerduty_json = get_oncall_from_json(pagerduty_reply, PAGER_DUTY_DATE_FORMAT, PAGER_DUTY_TIMEZONE)
        elif code == "4":
            error_msg = "{0}: Unauthorized, please double check that your Dev Token is valid.".format(
                status_code)
        elif code == "5":
            error_msg = "{0}: A 5xx server error occurred, please retry the request.".format(
                status_code)
        else:
            error_msg = "{0}: An unknown error has occurred.".format(status_code)
    except Exception:
        pass

    print("💻")
    print("---")
    if error_msg != "":
        pagerduty_json_last = load_last_pagerduty_reply(pagerduty_last_reply_file)
        try:
            pagerduty_json_last = load_last_pagerduty_reply(pagerduty_last_reply_file)
        except Exception:
            # Error not notable to report. First run never has a last file.
            pass
        print("Error: {0}".format(error_msg))
        print("RESPONSE STALE")
        print_xbar_oncalls(pagerduty_json_last, PAGER_DUTY_COMPANY)
    else:
        print_xbar_oncalls(pagerduty_json, PAGER_DUTY_COMPANY)
        save_last_pagerduty_reply(pagerduty_last_reply_file, pagerduty_json)
