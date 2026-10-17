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
        self.assertEqual(len(result['feed_errors']), 3)

    def test_no_leads_does_not_trigger_work(self):
        fixtures = {
            scout.TASKMARKET: {'tasks': [self.task(submissionCount=31)]},
            scout.RINER: {'tasks': []},
            scout.TASK_BOUNTY: {'data': []}
        }
        result = scout.scan(NOW, fetch=lambda url: fixtures[url])
        self.assertEqual(result['state'], 'complete')
        self.assertEqual(result['candidates'], [])

if __name__ == '__main__':
    unittest.main()
