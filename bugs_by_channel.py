#!/usr/bin/python3

import os
import re
import sys
import urllib.parse

import requests

#start = '2021-04-11'
#end = '2021-04-17'
start = sys.argv[1]
end = sys.argv[2]

# https://bugzilla.mozilla.org/buglist.cgi?o1=notequals&query_format=advanced&v1=%25group.mozilla-corporation%25&o2=notequals&v2=Mozilla&list_id=15689317&chfield=%5BBug%20creation%5D&chfieldfrom=2021-04-18&longdesc=User%20Agent%20Firefox%2F&f1=reporter&classification=Client%20Software&chfieldto=2021-04-24&f2=team_name&longdesc_initial=1&longdesc_type=allwordssubstr

# bugs filed by users between 'start' and 'end', with a user agent in the bug
# description
query = [
    ('Classification', 'Client Software'),
    ('chfield', '[Bug creation]'),
    ('chfieldfrom', start),
    ('chfieldto', end),
    ('f1', 'reporter'),
    ('o1', 'notequals'),
    ('v1', '%group.mozilla-corporation%'),
    ('f2', 'team_name'),
    ('o2', 'notequals'),
    ('v2', 'Mozilla'),
    ('longdesc', 'User Agent Firefox/'),
    ('longdesc_initial', 1),
    ('longdesc_type', 'allwordssubstr'),
    ('include_fields', 'description,id'),
#    ('bug_type', 'defect'),
#    ('count_only', 1),
#    ('keywords', 'regression'),
#    ('resolution', 'FIXED'),
]

token = os.environ['BMO_TOKEN']
url = 'https://bugzilla.mozilla.org/rest/bug?' + urllib.parse.urlencode(query)
bugs = requests.get(url, headers={'X-BUGZILLA-API-KEY': token}).json()

if bugs.get('error'):
    raise RuntimeError(bugs['message'])

#print("Found %s bugs" % bugs['bug_count'])
#sys.exit(0)
print("Found %s bugs" % len(bugs['bugs']))

version_re = re.compile('^User Agent.*Firefox/([0-9]*).0$')
def parse_version(comment):
    for line in comment.splitlines():
        m = version_re.match(line)
        if m is None:
            continue
        return int(m.group(1))
    print('skip %r' % comment)

channels = dict.fromkeys(['unknown', 'esr', 'release', 'beta', 'nightly'], 0)

for bug in bugs['bugs']:
    version = parse_version(bug['description'])
    if version is None:
        channels['unknown'] += 1
    elif version == 78:
        #print('ESR', bug['id'])
        channels['esr'] += 1
    elif version < 88:
        #print('RELEASE', bug['id'], version)
        channels['release'] += 1
    elif version < 89:
        #print('BETA', bug['id'], version)
        channels['beta'] += 1
    else:
        #print('NIGHTLY', bug['id'], version)
        channels['nightly'] += 1

print(channels)
