#!/usr/bin/python3

import datetime
import urllib.parse

import requests

# release -> start of its nightly cycle
DATES = {
#    63: '2018-06-25',
#    64: '2018-09-04',
#    65: '2018-10-22',
#    66: '2018-12-10',
#    67: '2019-01-28',
#    68: '2019-03-18',
#    69: '2019-05-13',
#    70: '2019-07-08',
#    71: '2019-09-02',
#    72: '2019-10-21',
#    73: '2019-12-02',
#    74: '2020-01-06',
#    75: '2020-02-10',
#    76: '2020-03-09',

# 77 is around when we started using severity
    77: '2020-04-06',
    78: '2020-05-04',
    79: '2020-06-01',
    80: '2020-06-29',
    81: '2020-07-27',
    82: '2020-08-24',
    83: '2020-09-21',
    84: '2020-10-19',
    85: '2020-11-16',
    86: '2020-12-14',
    87: '2021-01-25',
    88: '2021-02-22',
    89: '2021-03-22',
    90: '2021-04-19',
    91: '2021-05-31',
    92: '2021-07-12',
    93: '2021-08-09',
    94: '2021-09-06',
    95: '2021-10-04',
    96: '2021-11-01',
    97: '2021-12-06',
    98: '2022-01-10',
    99: '2022-02-07',
   100: '2022-03-07',
}

for release in DATES:
    if DATES[release + 2] > datetime.date.today().strftime('%Y-%m-%d'):
        break
    beta_start = DATES[release + 1]
    beta_end = DATES[release + 2]
    query = urllib.parse.urlencode([
        ('chfieldfrom', beta_start),
        ('chfieldto', beta_end),
        ('chfield', 'flagtypes.name'),
        ('chfieldvalue', 'approval-mozilla-beta+'),
        ('bug_severity', 'S1'),
        ('bug_severity', 'S2'),
    ])
    buglist_url = 'https://bugzilla.mozilla.org/buglist.cgi?' + query
    rest_url = 'https://bugzilla.mozilla.org/rest/bug?count_only=1&' + query
    print('%s,%s,%s' % (release, requests.get(rest_url).json()['bug_count'], buglist_url))

# 88: https://bugzilla.mozilla.org/buglist.cgi?chfieldfrom=2021-03-23&bug_severity=S1&bug_severity=S2&chfield=flagtypes.name&chfieldvalue=approval-mozilla-beta%2B&list_id=15689147&chfieldto=2021-04-19&query_format=advanced
