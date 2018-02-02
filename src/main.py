#!/usr/bin/env python

import hmac
import json
import os
import subprocess
import sys

from flask import Flask, request, abort
import requests

class dictToObject(object):
    def __init__(self, d):
        for key, value in d.items():
            if isinstance(value, (list, tuple)):
               setattr(self, key, [dictToObject(x) if isinstance(x, dict) else x for x in value])
            else:
               setattr(self, key, dictToObject(value) if isinstance(value, dict) else value)

def ghRequestPost(url, json):
    return requests.post(url,
        headers={'Authorization': 'token ' + ghToken},
        json=json)

ghTargetUser = os.environ.get('GH_TARGET_USER')
ghUser = os.environ.get('GH_USER')
ghToken = os.environ.get('GH_TOKEN')
ghSecretVerify = os.environ.get('GH_SECRET_VERIFY')

app = Flask(__name__)

@app.route('/github_hook', methods=['POST'])
def githubHook():

    headerSignature = request.headers.get('X-Hub-Signature')
    if headerSignature is None:
        abort(403)

    hashName, signature = headerSignature.split('=')
    if hashName != 'sha1':
        abort(501)

    hmacValue = hmac.new(ghSecretVerify.encode('utf8'), msg=request.data, digestmod='sha1')

    if not hmac.compare_digest(str(hmacValue.hexdigest()), str(signature)):
        abort(403)

    event = request.headers.get('X-GitHub-Event', 'ping')
    data = dictToObject(request.get_json())

    if event == 'ping':
        return json.dumps({'msg': 'pong'})
    elif event == 'create':
        return githubEventCreate(data)

    return json.dumps({'status': 'done'})

def githubEventCreate(data):
    if data.ref_type != 'tag':
        return json.dumps({'status': 'done'})

    os.chdir('/app/')

    args = ['bash', './src/create_merge_branches.sh', data.ref]
    print('running: ', ' '.join(args))

    try:
        print(subprocess.check_output(args).decode('ascii', errors='surrogateescape'))
    except subprocess.CalledProcessError as ex:
        print(ex.output.decode('ascii', errors='surrogateescape'))
        return json.dumps({'status': 'fail'})

    for repo in ['DCD', 'D-Scanner', 'dfmt']:
        res = ghRequestPost('https://api.github.com/repos/{}/{}/pulls'.format(ghTargetUser, repo),
            json={
                'title': 'Update dlibparse to ' + data.ref,
                'head': ghUser + ':merge-libdparse-' + data.ref,
                'base': 'master',
                'body': 'beep boop',
            })

        # TODO possibly handle case where multiple attempts can be made over time
        if res.status_code != requests.codes.created:
            print("Failed to create pull request:\n", res)
            return json.dumps({'status': 'done'})

        values = dictToObject(res.json())

        res = ghRequestPost(values.issue_url + '/labels', json=['auto-merge'])
        if res.status_code != requests.codes.ok:
            print("Failed to create label:\n", res)
            continue

    return json.dumps({'status': 'done'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

