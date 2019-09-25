#!/usr/bin/python3

import json
import requests

# TODO parse this from the wiki? :(
# release -> date its nightly cycle started
dates = {
    63: '2018-06-25',
    64: '2018-09-04',
    65: '2018-10-22',
    66: '2018-12-10',
    67: '2019-01-28',
    68: '2019-03-18',
    69: '2019-05-20',
    70: '2019-07-08',
    71: '2019-09-02',
    72: '2019-10-21',
    73: '2019-12-02',
    74: '2020-01-06',
}

bmo = 'https://bugzilla.mozilla.org/rest/bug?count_only=1&'

# new regressions filed during nightly
nightly_regressions_template = "keywords=regression&o1=anyexact&o2=notequals&chfield=%5BBug%20creation%5D&chfieldfrom={NIGHTLY_START}&o4=notequals&v1=disabled%2Cunaffected%2C---&v2=disabled&v4=---&f1=cf_status_firefox{OLDRELEASE}&o3=notequals&v3=unaffected&resolution=---&resolution=FIXED&f4=cf_status_firefox{RELEASE}&chfieldto={NIGHTLY_END}&f3=cf_status_firefox{RELEASE}&f2=cf_status_firefox{RELEASE}"
# new regressions, filed during beta
beta_regressions_template = "keywords=regression&o1=anyexact&o2=notequals&chfield=%5BBug%20creation%5D&chfieldfrom={BETA_START}&o4=notequals&v1=disabled%2Cunaffected%2C---&v2=disabled&v4=---&f1=cf_status_firefox{OLDRELEASE}&o3=notequals&v3=unaffected&resolution=---&resolution=FIXED&f4=cf_status_firefox{RELEASE}&chfieldto={BETA_END}&f3=cf_status_firefox{RELEASE}&f2=cf_status_firefox{RELEASE}"
# new regressions, filed before release, unfixed in that release
unfixed_regressions_template = "keywords=regression&chfield=%5BBug%20creation%5D&chfieldfrom={NIGHTLY_START}&chfieldto={BETA_END}&o1=anyexact&f1=cf_status_firefox{OLDRELEASE}&v1=disabled%2Cunaffected%2C---&o2=anyexact&f2=cf_status_firefox{RELEASE}&v2=fixed%2Cverified%2Cwontfix&resolution=---&resolution=FIXED"

# test
for v in range(68, 71):
    nightly = requests.get(bmo + nightly_regressions_template.format(RELEASE=v, OLDRELEASE=v-1, NIGHTLY_START=dates[v], NIGHTLY_END=dates[v+1]))
    nightly.raise_for_status()
    beta = requests.get(bmo + beta_regressions_template.format(RELEASE=v, OLDRELEASE=v-1, BETA_START=dates[v+1], BETA_END=dates[v+2]))
    beta.raise_for_status()
    unfixed = requests.get(bmo + unfixed_regressions_template.format(RELEASE=v, OLDRELEASE=v-1, NIGHTLY_START=dates[v], BETA_END=dates[v+2]))
    unfixed.raise_for_status()
    print('new regressions filed in %d: nightly %d\tbeta %d\tunfixed %d' % (v, nightly.json()['bug_count'], beta.json()['bug_count'], unfixed.json()['bug_count']))
