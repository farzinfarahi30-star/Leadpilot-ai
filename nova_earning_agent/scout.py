"""Read-only NOVA public task scout. Candidate listings are NOT confirmed payments.
No authentication, signing, task acceptance, advertising or spending.
Feed failures are errors, never reported as zero available tasks.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any

TASKMARKET = 'https://api.taskmarket.dev/api/tasks?status=open&limit=50'
RINER = 'https://api.riner.io/api/v1/tasks?limit=50'
TASK_BOUNTY = 'https://www.task-bounty.com/api/v1/tasks'
JOBBI = 'https://jobbi.org/gigs.json?lane=agent&min_reward=20&limit=150'
BLOCKED = re.compile(
    r'\b(?:promotion|promote|viral|followers|likes|bot accounts|referral|invest|'
    r'token launch|buy tokens|fake|spam|impersonat|post on|publications|twitter|'
    r'instagram|telegram|discord|reddit|medium|dev\.to|bluesky|wallet address|'
    r'wallet binding|staking|bond|gas fee|kyc|airdrop|market cap)\b', re.I)


@dataclass(frozen=True)
class Candidate:
    source: str
    identifier: str
    reward_usd: float
    description: str
    link: str
    closing_utc: str
    evidence: str


def fetch_json(url: str) -> Any:
    request = urllib.request.Request(
        url, headers={'User-Agent': 'NovaPublicTaskScout/0.1 (read-only)',
                      'Accept': 'application/json'})
    with urllib.request.urlopen(request, timeout=14) as response:
        if response.status != 200:
            raise ValueError(f'HTTP {response.status} from {url}')
        return json.load(response)


def future_hours(value: str, now: dt.datetime) -> float:
    if not isinstance(value, str) or not value:
        return 0.0
    try:
        when = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
        return (when - now).total_seconds() / 3600
    except (ValueError, TypeError):
        return 0.0


def taskmarket_candidates(payload: Any, now: dt.datetime) -> list[Candidate]:
    if not isinstance(payload, dict) or not isinstance(payload.get('tasks'), list):
        raise ValueError('Unrecognized TaskMarket data; never infer zero open tasks')
    found: list[Candidate] = []
    for t in payload['tasks']:
        if not isinstance(t, dict) or t.get('status') != 'open' or t.get('submissionWindowOpen') is not True:
            continue
        if t.get('stakeRequired') is not False or t.get('hasAccessPassword') is not False:
            continue
        tx = t.get('escrowTxHash')
        if not isinstance(tx, str) or not re.fullmatch(r'0x[a-fA-F0-9]{64}', tx):
            continue
        if t.get('submissionCount', 999) > 2 or t.get('awardCount', 0) != 0:
            continue
        if future_hours(t.get('expiryTime', ''), now) < 12:
            continue
        description = str(t.get('description', ''))[:5000]
        if BLOCKED.search(description):
            continue
        reward = float(t.get('netReward') or 0) / 1000000
        if reward < 5:
            continue
        code = str(t.get('referenceCode') or t.get('id') or '')
        if not code.startswith('TSK-'):
            continue
        found.append(Candidate(
            'TaskMarket', code, reward, description[:350], 'https://taskmarket.dev/',
            t['expiryTime'],
            f'Listed escrow transaction {tx}. Chain balance and actual payout NOT verified. '
            f'Winner-only risk; {t.get("submissionCount", 0)} submissions.'))
    return found


def riner_candidates(payload: Any, now: dt.datetime) -> list[Candidate]:
    if not isinstance(payload, dict) or not isinstance(payload.get('tasks'), list):
        raise ValueError('Unrecognized Riner data')
    found: list[Candidate] = []
    for t in payload['tasks']:
        if not isinstance(t, dict) or t.get('status') != 'published' or t.get('assigned_agent_id'):
            continue
        if t.get('selection_mode') != 'first_come' or t.get('max_applicants') != 1:
            continue
        if t.get('budget_token') != 'USDC' or float(t.get('budget_amount') or 0) < 5:
            continue
        if not re.fullmatch(r'0x[a-fA-F0-9]{64}', str(t.get('escrow_tx') or '')):
            continue
        if future_hours(t.get('deadline', ''), now) < 12:
            continue
        description = str(t.get('description', ''))
        if BLOCKED.search(description):
            continue
        found.append(Candidate(
            'Riner', str(t.get('id')), float(t['budget_amount']), description[:350],
            'https://riner.io/tasks', t['deadline'],
            'Listed escrow tx; actual payout and current availability NOT verified.'))
    return found


def jobbi_candidates(payload: Any, now: dt.datetime) -> list[Candidate]:
    """Conservatively shortlist recent escrow-listed programming bounties.
    Source is a third-party index; each listing needs primary-source verification.
    """
    if not isinstance(payload, dict) or not isinstance(payload.get('items'), list):
        raise ValueError('Unrecognized Jobbi JSON Feed: cannot infer zero tasks')
    found: list[Candidate] = []
    for item in payload['items']:
        if not isinstance(item, dict):
            continue
        meta = item.get('_jobbi', {})
        if not isinstance(meta, dict):
            continue
        if meta.get('lane') != 'agent' or meta.get('claims_open') is not True:
            continue
        if meta.get('payment_state') != 'escrowed':
            continue
        if meta.get('payout_grade') not in ('A', 'A-', 'B', 'B-', 'C+', 'C'):
            continue
        if meta.get('source') not in ('bountyhub', 'algora', 'frantic'):
            continue
        reward = meta.get('reward') or {}
        if not isinstance(reward, dict):
            continue
        if reward.get('currency') not in ('USD', 'USDC'):
            continue
        amount = float(reward.get('amount') or 0)
        if amount < 20 or amount > 3000:
            continue
        link = str(item.get('url') or '')
        if not link.startswith('https://'):
            continue
        published = str(item.get('date_published') or '')
        modified = str(item.get('date_modified') or '')
        pub_age = -future_hours(published, now)
        mod_age = -future_hours(modified, now)
        if not (0 <= pub_age <= 24 * 30 and 0 <= mod_age <= 24 * 14):
            continue
        title = str(item.get('title') or '')
        description = str(item.get('content_text') or '')
        if BLOCKED.search(title + ' ' + description):
            continue
        evidence = (
            'Third-party Jobbi index labels this escrowed, not independently confirmed. '
            f'Source={meta.get("source")} grade={meta.get("payout_grade")}; '
            'verify issue state, funder, escrow, assignment, open claims, '
            'competing PRs, and exact payout eligibility before beginning.'
        )
        found.append(Candidate(
            str(meta['source']), str(item.get('id') or link), amount,
            (title + ': ' + description)[:350], link,
            str(meta.get('expires') or 'unspecified'), evidence))
    return found


def scan(now: dt.datetime | None = None, fetch=fetch_json) -> dict:
    now = now or dt.datetime.now(dt.timezone.utc)
    feeds = [
        ('taskmarket', TASKMARKET, taskmarket_candidates),
        ('riner', RINER, riner_candidates),
        ('task_bounty', TASK_BOUNTY, None),
        ('jobbi', JOBBI, jobbi_candidates),
    ]
    results: list[Candidate] = []
    errors: dict[str, str] = {}
    counts: dict[str, int | None] = {}
    for name, url, parse in feeds:
        try:
            data = fetch(url)
            if name == 'task_bounty':
                if not isinstance(data, dict) or not isinstance(data.get('data'), list):
                    raise ValueError('Unrecognized task-bounty feed')
                counts[name] = len(data['data'])
                continue
            if name == 'jobbi':
                if not isinstance(data, dict) or not isinstance(data.get('items'), list):
                    raise ValueError('Unrecognized Jobbi feed')
                counts[name] = len(data['items'])
                results += parse(data, now)
                continue
            if not isinstance(data, dict) or not isinstance(data.get('tasks'), list):
                raise ValueError('Unrecognized task feed')
            counts[name] = len(data['tasks'])
            results += parse(data, now)
        except (urllib.error.URLError, TimeoutError, ValueError, TypeError,
                KeyError, OSError) as exc:
            errors[name] = str(exc)[:220]
            counts[name] = None
    return {
        'checked_at_utc': now.isoformat(),
        'state': 'partial' if errors else 'complete',
        'feed_counts': counts, 'feed_errors': errors,
        'candidates': [asdict(c) for c in results],
        'note': 'Candidate is NOT verified escrow, an accepted contract, payment, balance, '
                'or expected earnings. Independently verify buyer, escrow and payout '
                'before acceptance.'
    }


def main() -> None:
    result = scan()
    os.makedirs('reports', exist_ok=True)
    with open('reports/public-paid-task-scout.json', 'w', encoding='utf-8') as file:
        json.dump(result, file, indent=2, ensure_ascii=False)
    print(json.dumps({'state': result['state'], 'feed_counts': result['feed_counts'],
                      'feed_errors': result['feed_errors'],
                      'candidates': len(result['candidates'])}, indent=2))
    if not any(value is not None for value in result['feed_counts'].values()):
        raise SystemExit('All external feeds failed; no conclusion possible')


if __name__ == '__main__':
    main()
