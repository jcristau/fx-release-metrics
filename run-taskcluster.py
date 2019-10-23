#!/usr/bin/python3

import datetime
import json
import os
import subprocess
import sys

import requests

# TODO parse this from the wiki? :(
# release -> date its nightly cycle started
DATES = {
    63: '2018-06-25',
    64: '2018-09-04',
    65: '2018-10-22',
    66: '2018-12-10',
    67: '2019-01-28',
    68: '2019-03-18',
    69: '2019-05-13',
    70: '2019-07-08',
    71: '2019-09-02',
    72: '2019-10-21',
    73: '2019-12-02',
    74: '2020-01-06',
}

for version in DATES:
    if DATES[version] > datetime.date.today().strftime('%Y-%m-%d'):
        nightly = version - 1
        beta = version - 2
        release = version - 3
        break
else:
    print("Don't know when the current nightly cycle will end, aborting.", file=sys.stderr)
    sys.exit(1)


def setup():
    os.mkdir('/srv/work')
    os.chdir('/srv/work')
    subprocess.check_call(['hg', 'clone', 'https://hg.mozilla.org/hgcustom/version-control-tools'])
    with open('/etc/mercurial/hgrc.d/vct.rc', 'w') as f:
        f.write('''\
[extensions]
# mozext comes before pushlog so pushlog's conflicting revset stuff takes precedence
mozext = /srv/work/version-control-tools/hgext/mozext
pushlog = /srv/work/version-control-tools/hgext/pushlog
firefoxtree = /srv/work/version-control-tools/hgext/firefoxtree
''')
    subprocess.check_call(['hg', 'clone', 'https://hg.mozilla.org/mozilla-unified'])
    subprocess.check_call(['hg', 'clone', 'https://hg.mozilla.org/mozilla-central'])

mc = 'mozilla-central'
mu = 'mozilla-unified'

# backouts

def nightly_backouts(v):
    backout_changesets = subprocess.check_output(['hg', 'log',
            '-r', 'FIREFOX_NIGHTLY_%d_END::(present(FIREFOX_NIGHTLY_%d_END) or tip) and pushhead()' % (v-1, v),
            '--template', "{if(backsoutnodes, ifeq(node, pushbasenode, '{node|short} {desc|firstline}\n', ''))}"],
            cwd='mozilla-central').splitlines()
    return backout_changesets

# features

def count_planned_features(v):
    # XXX requires trello api key, skipping for now
    pass

# regressions

bmo = 'https://bugzilla.mozilla.org/rest/bug?include_fields=id&'
# XXX count_only=1&

# new regressions
new_regressions_template = (
    "keywords=regression&chfield=%5BBug%20creation%5D&chfieldfrom={START_DATE}&chfieldto={END_DATE}&"
    "resolution=---&resolution=FIXED&"
    "f1=cf_status_firefox{PREVIOUS_VERSION}&o1=anyexact&v1=disabled%2Cunaffected%2C---&"
    "f2=cf_status_firefox{VERSION}&o2=notequals&v2=disabled&"
    "f3=cf_status_firefox{VERSION}&o3=notequals&v3=unaffected&"
    "f4=cf_status_firefox{VERSION}&o4=notequals&v4=---")
# new regressions, filed before release, unfixed in that release
unfixed_regressions_template = (
    "keywords=regression&chfield=%5BBug%20creation%5D&chfieldfrom={NIGHTLY_START}&chfieldto={BETA_END}&"
    "resolution=---&resolution=FIXED&"
    "o1=anyexact&f1=cf_status_firefox{OLDRELEASE}&v1=disabled%2Cunaffected%2C---&"
    "o2=anyexact&f2=cf_status_firefox{RELEASE}&v2=fixed%2Cverified%2Cwontfix")
unfixed_regressions_notp5_template = unfixed_regressions_template + (
    "&f3=priority&o3=notequals&v3=P5")

def beta_regressions(v):
    # new regressions in version v, filed while v was on beta
    r = requests.get(bmo + new_regressions_template.format(VERSION=v, PREVIOUS_VERSION=v-1, START_DATE=DATES[v+1], END_DATE=DATES[v+2]))
    r.raise_for_status()
    return [b['id'] for b in r.json()['bugs']]

def nightly_regressions(v):
    # new regressions in version v, filed while v was on nightly
    r = requests.get(bmo + new_regressions_template.format(VERSION=v, PREVIOUS_VERSION=v-1, START_DATE=DATES[v], END_DATE=DATES[v+1]))
    r.raise_for_status()
    return [b['id'] for b in r.json()['bugs']]

def unfixed_new_regressions(v):
    r = requests.get(bmo + unfixed_regressions_template.format(RELEASE=v, OLDRELEASE=v-1, NIGHTLY_START=DATES[v], BETA_END=DATES[v+2]))
    r.raise_for_status()
    return [b['id'] for b in r.json()['bugs']]

def unfixed_new_regressions_notp5(v):
    r = requests.get(bmo + unfixed_regressions_notp5_template.format(RELEASE=v, OLDRELEASE=v-1, NIGHTLY_START=DATES[v], BETA_END=DATES[v+2]))
    r.raise_for_status()
    return [b['id'] for b in r.json()['bugs']]

# uplifts

def beta_uplifts(v):
    uplifts = subprocess.check_output(['hg', 'log',
        '-r', 'first(present(FIREFOX_NIGHTLY_{version:d}_END) or central)::first(present(FIREFOX_BETA_{version:d}_END) or beta) and desc("re:(?i)^bug") and not desc("re:(?i)a=(release|npotb|test)")'.format(version=v),
        '--template', '{desc|firstline}\\n'], cwd=mu)
    bugs = uplifts.split
    bugs = set(line.split()[1].decode('ascii') for line in uplifts.splitlines() if b'a=release' not in line.lower() and b'a=test' not in line.lower() and b'a=npotb' not in line.lower())
    return bugs


def main():
    artifact_url = os.environ.get('PREVIOUS_RESULTS')
    if artifact_url is None:
        results = []
    else:
        r = requests.get(os.environ['PREVIOUS_RESULTS'])
        try:
            r.raise_for_status()
        except Exception:
            results = []
        else:
            results = r.json()
    setup()
    backouts = nightly_backouts(nightly)
    beta_bugs = beta_regressions(beta)
    nightly_bugs = nightly_regressions(nightly)
    unfixed_nightly = unfixed_new_regressions(nightly)
    unfixed_beta = unfixed_new_regressions(beta)
    unfixed_nightly_notp5 = unfixed_new_regressions_notp5(nightly)
    unfixed_beta_notp5 = unfixed_new_regressions_notp5(beta)
    uplifts = beta_uplifts(beta)
    results.append(
        {
            'date': datetime.date.today().strftime('%Y-%m-%d'),
            'nightly': nightly,
            'beta': beta,
            'release': release,
            'beta_regressions': [
                len(beta_bugs),
                'https://bugzilla.mozilla.org/buglist.cgi?bug_id={}'.format(
                    ','.join(str(b) for b in beta_bugs))],
            'nightly_regressions': [
                len(nightly_bugs),
                'https://bugzilla.mozilla.org/buglist.cgi?bug_id={}'.format(
                    ','.join(str(b) for b in nightly_bugs))],
            'unfixed_beta_regressions': [
                len(unfixed_beta),
                'https://bugzilla.mozilla.org/buglist.cgi?bug_id={}'.format(
                    ','.join(str(b) for b in unfixed_beta))],
            'unfixed_beta_regressions_notp5': [
                len(unfixed_beta_notp5),
                'https://bugzilla.mozilla.org/buglist.cgi?bug_id={}'.format(
                    ','.join(str(b) for b in unfixed_beta_notp5))],
            'unfixed_nightly_regressions': [
                len(unfixed_nightly),
                'https://bugzilla.mozilla.org/buglist.cgi?bug_id={}'.format(
                    ','.join(str(b) for b in unfixed_nightly))],
            'unfixed_nightly_regressions_notp5': [
                len(unfixed_nightly_notp5),
                'https://bugzilla.mozilla.org/buglist.cgi?bug_id={}'.format(
                    ','.join(str(b) for b in unfixed_nightly_notp5))],
            'beta_uplifts': [len(uplifts), list(uplifts)],
        })
    with open('/results.json', 'w') as f:
        json.dump(results, f)
    json.dump(results, sys.stdout)

if __name__ == '__main__':
    main()
