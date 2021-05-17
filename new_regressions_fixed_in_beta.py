#!/usr/bin/python3

import datetime
import urllib.parse

import requests

# release -> start of its nightly cycle
DATES = {
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
    for severity in (None, 'S1', 'S2', 'S3', 'S4'):
        params = [
            ('chfieldfrom', beta_start),
            ('chfieldto', beta_end),
            ('chfield', 'flagtypes.name'),
            ('chfieldvalue', 'approval-mozilla-beta+'),
            ('keywords', 'regression'),
            ('f1', 'cf_status_firefox%d' % (release - 1)),
            ('o1', 'anywords'),
            ('v1', 'unaffected,disabled,---'),
        ]
        if severity:
            params.append(('severity', severity))
        query = urllib.parse.urlencode(params)
        buglist_url = 'https://bugzilla.mozilla.org/buglist.cgi?' + query
        rest_url = 'https://bugzilla.mozilla.org/rest/bug?count_only=1&' + query
        print('%s,%s,%s,%s' % (release, severity or 'any', requests.get(rest_url).json()['bug_count'], buglist_url))

