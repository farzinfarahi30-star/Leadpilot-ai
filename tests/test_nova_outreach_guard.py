import importlib.util
import tempfile
import threading
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'tools' / 'nova_outreach_guard.py'
spec = importlib.util.spec_from_file_location('nova_outreach_guard', SCRIPT)
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dbpath = Path(self.tmp.name) / 'guard.sqlite3'
        self.db = g.connect(self.dbpath)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_suppression_case_insensitive(self):
        g.suppress(self.db, ' Stop@Example.com ', 'opted out')
        self.assertEqual(g.reserve(self.db, 'STOP@example.com', 'c1', 'body')['reason'], 'suppressed: opted out')

    def test_reservation_and_cooldown(self):
        r = g.reserve(self.db, 'buyer@example.com', 'offer', 'Intro')
        self.assertTrue(r['allowed'])
        self.assertEqual(g.reserve(self.db, 'buyer@example.com', 'another', 'Other')['reason'], 'outstanding_reservation')
        self.assertEqual(g.finalize(self.db, r['reservation_token'], 'sent')['status'], 'sent')
        self.assertEqual(g.reserve(self.db, 'buyer@example.com', 'different', 'Other')['reason'], 'cooldown_active')
        self.assertFalse(g.finalize(self.db, r['reservation_token'], 'sent')['ok'])

    def test_cancel_only_when_not_sent(self):
        r = g.reserve(self.db, 'buyer@example.com', 'offer', 'Intro')
        self.assertTrue(g.finalize(self.db, r['reservation_token'], 'cancelled')['ok'])
        self.assertTrue(g.reserve(self.db, 'buyer@example.com', 'offer', 'Intro')['allowed'])

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            g.reserve(self.db, 'notanemail', 'sales', 'text')
        with self.assertRaises(ValueError):
            g.reserve(self.db, 'buyer@example.com', 'sales', '  ')
        with self.assertRaises(ValueError):
            g.check_block(self.db, 'buyer@example.com', 0)

    def test_concurrent_workers_one_reservation(self):
        barrier = threading.Barrier(8)
        results = []
        lock = threading.Lock()
        def worker(i):
            db = g.connect(self.dbpath)
            barrier.wait()
            result = g.reserve(db, 'buyer@example.com', 'multiworker', f'message {i}')
            with lock:
                results.append(result)
            db.close()
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
        for t in threads: t.start()
        for t in threads: t.join()
        self.assertEqual(sum(r['allowed'] for r in results), 1)
        self.assertEqual(len(results), 8)


if __name__ == '__main__':
    unittest.main()
