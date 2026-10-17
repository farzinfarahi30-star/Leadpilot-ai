import datetime as dt
import unittest
import scout

NOW = dt.datetime(2026, 10, 18, tzinfo=dt.timezone.utc)


class ScoutTests(unittest.TestCase):
    def task(self, **changes):
        record = dict(
            status='open', submissionWindowOpen=True, stakeRequired=False,
            hasAccessPassword=False, escrowTxHash='0x' + '1' * 64,
            referenceCode='TSK-TEST', netReward='12000000',
            description='Build a tested Python parser for supplied CSV data.',
            expiryTime='2026-10-20T12:00:00Z', submissionCount=0, awardCount=0
        )
        record.update(changes)
        return record

    def test_low_competition_opportunity_needs_independent_payment_proof(self):
        candidates = scout.taskmarket_candidates({'tasks': [self.task()]}, NOW)
        self.assertEqual(len(candidates), 1)
        self.assertIn('NOT verified', candidates[0].evidence)

    def test_marketing_spam_is_excluded(self):
        self.assertEqual(scout.taskmarket_candidates({
            'tasks': [self.task(description='Post on Reddit to promote tokens')]
        }, NOW), [])

    def test_competition_filter(self):
        self.assertEqual(scout.taskmarket_candidates({
            'tasks': [self.task(submissionCount=12)]
        }, NOW), [])

    def test_escrow_metadata_required(self):
        self.assertEqual(scout.taskmarket_candidates({
            'tasks': [self.task(escrowTxHash='missing')]
        }, NOW), [])

    def test_expired_excluded(self):
        self.assertEqual(scout.taskmarket_candidates({
            'tasks': [self.task(expiryTime='2026-10-17T11:00:00Z')]
        }, NOW), [])

    def test_first_come_task_filter(self):
        record = dict(
            status='published', assigned_agent_id=None, selection_mode='first_come',
            max_applicants=1, budget_token='USDC', budget_amount=10,
            escrow_tx='0x' + 'e' * 64, deadline='2026-10-23T00:00:00Z',
            description='Write documentation and automated tests', id='task1'
        )
        self.assertEqual(len(scout.riner_candidates({'tasks': [record]}, NOW)), 1)
        record['selection_mode'] = 'manual'
        self.assertEqual(scout.riner_candidates({'tasks': [record]}, NOW), [])

    def test_invalid_feeds_do_not_become_zero_opportunities(self):
        with self.assertRaises(ValueError):
            scout.taskmarket_candidates({}, NOW)
        def fail(_url):
            raise OSError('offline')
        result = scout.scan(NOW, fetch=fail)
        self.assertEqual(result['state'], 'partial')
        self.assertEqual(len(result['feed_errors']), 4)

    def jobbi_item(self, **changes):
        meta = {
            'lane': 'agent', 'claims_open': True, 'payment_state': 'escrowed',
            'payout_grade': 'B', 'source': 'bountyhub',
            'reward': {'amount': 100, 'currency': 'USD', 'rail': 'stripe'},
            'expires': None,
        }
        item = {
            'id': 'bountyhub:open-issue-1', 'url': 'https://github.com/org/repo/issues/12',
            'title': 'Fix tested TypeScript parser', 'content_text': 'Build a parser and tests',
            'date_published': '2026-10-16T12:00:00Z',
            'date_modified': '2026-10-17T19:00:00Z',
            '_jobbi': meta,
        }
        for k, v in changes.items():
            if k.startswith('meta_'):
                meta[k[5:]] = v
            else:
                item[k] = v
        return item

    def test_jobbi_recent_escrow_listing_is_review_candidate_not_income(self):
        candidates = scout.jobbi_candidates({'items': [self.jobbi_item()]}, NOW)
        self.assertEqual(len(candidates), 1)
        self.assertIn('not independently confirmed', candidates[0].evidence)

    def test_jobbi_rejects_promises_and_old_issues(self):
        promised = self.jobbi_item(meta_payment_state='promised')
        stale = self.jobbi_item(date_published='2025-12-01T12:00:00Z')
        bonds = self.jobbi_item(content_text='Pay a bond before coding')
        self.assertEqual(scout.jobbi_candidates(
            {'items': [promised, stale, bonds]}, NOW), [])

    def test_jobbi_rejects_unrecognized_feed_and_deceptive_tasks(self):
        with self.assertRaises(ValueError):
            scout.jobbi_candidates({}, NOW)
        bad = self.jobbi_item(title='Promote token airdrop')
        self.assertEqual(scout.jobbi_candidates({'items': [bad]}, NOW), [])

    def test_no_leads_does_not_trigger_work(self):
        fixtures = {
            scout.TASKMARKET: {'tasks': [self.task(submissionCount=31)]},
            scout.RINER: {'tasks': []},
            scout.TASK_BOUNTY: {'data': []},
            scout.JOBBI: {'items': []}
        }
        result = scout.scan(NOW, fetch=lambda url: fixtures[url])
        self.assertEqual(result['state'], 'complete')
        self.assertEqual(result['candidates'], [])

if __name__ == '__main__':
    unittest.main()
