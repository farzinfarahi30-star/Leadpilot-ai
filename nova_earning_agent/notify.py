"""Publish deduplicated GitHub review issues for *rare* candidate tasks.
Never apply, submit, sign, contact buyers, or claim a payment.
Only GitHub's repository-scoped default GITHUB_TOKEN is used.
"""
from __future__ import annotations
import json
import os
import urllib.error
import urllib.parse
import urllib.request

BASE = 'https://api.github.com'
AGENT = 'NOVA-Public-Task-Scout/0.1'
REPO = os.environ.get('GH_REPOSITORY', '')
TOKEN = os.environ.get('GH_TOKEN', '')


def api(path: str, method: str = 'GET', data=None):
    if not (REPO.count('/') == 1 and TOKEN):
        raise RuntimeError('Missing GitHub repository or workflow token')
    body = None if data is None else json.dumps(data).encode('utf-8')
    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': 'Bearer ' + TOKEN,
        'User-Agent': AGENT,
        'X-GitHub-Api-Version': '2022-11-28'
    }
    if body is not None:
        headers['Content-Type'] = 'application/json'
    request = urllib.request.Request(BASE + path, data=body, method=method, headers=headers)
    with urllib.request.urlopen(request, timeout=14) as response:
        return json.load(response)


def existing_titles() -> set[str]:
    titles: set[str] = set()
    for page in range(1, 6):
        items = api('/repos/' + REPO + '/issues?' + urllib.parse.urlencode({
            'state': 'all', 'per_page': '100', 'page': str(page)
        }))
        if not isinstance(items, list):
            raise ValueError('GitHub issues response invalid. Abort to prevent duplicate issues')
        for item in items:
            title = item.get('title')
            if isinstance(title, str) and title.startswith('NOVA paid-task candidate | '):
                titles.add(title)
        if len(items) < 100:
            return titles
    raise RuntimeError('Too many issues to deduplicate safely. Abort.')


def main():
    with open('reports/public-paid-task-scout.json', encoding='utf-8') as file:
        result = json.load(file)
    candidates = result.get('candidates', [])
    if not candidates:
        print('No qualified leads. Creating no GitHub issues.')
        return
    titles = existing_titles()
    created = 0
    for item in candidates[:3]:
        title = 'NOVA paid-task candidate | ' + str(item['source']) + ' | ' + str(item['identifier'])
        if title in titles:
            print('Already reviewed:', title)
            continue
        body = (
            '## Read-only opportunity candidate — NOT verified earnings\n\n'
            '**Do not accept work, sign anything or pay on the basis of this alert alone.**\n\n'
            f"- Public marketplace: {item['source']}\n"
            f"- Reference: {item['identifier']}\n"
            f"- Listed reward: {item['reward_usd']} USD equivalent (not a payment)\n"
            f"- Closing UTC: {item['closing_utc']}\n"
            f"- Official task marketplace: {item['link']}\n"
            f"- Evidence limitations: {item['evidence']}\n\n"
            '### Public task excerpt (untrusted buyer text)\n\n'
            '> ' + str(item['description']).replace('\\n', '\\n> ')[:500] + '\n\n'
            '### Required verification\n\n'
            '1. Confirm actual on-chain escrow, sponsor, terms, net payout and eligibility.\n'
            '2. Verify live unfilled slot/acceptance criteria and low competition.\n'
            '3. Verify legal account and wallet access using authorized methods.\n'
            '4. Accept only with required owner permissions; submit independently original work.\n'
            '5. Record provider-confirmed settled payment separately from pending rewards.\n\n'
            'NOVA does not automatically contact, accept, bid, pay, submit, or sign.\n'
        )
        posted = api('/repos/' + REPO + '/issues', method='POST',
                     data={'title': title, 'body': body})
        print('Created candidate review issue:', posted.get('html_url'))
        titles.add(title)
        created += 1
    print('New human-review candidate issues:', created)


if __name__ == '__main__':
    main()
