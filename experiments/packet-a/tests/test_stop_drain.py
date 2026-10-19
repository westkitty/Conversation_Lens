"""Deterministic stop/race tests; no microphone or model installation required."""
import importlib.util
from hashlib import sha256
from pathlib import Path
import threading
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'lens_stop_drain.py'
spec = importlib.util.spec_from_file_location('lens_stop_drain', SOURCE)
mod = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
C = mod.CaptureDrainCoordinator
LeaseConflict = mod.LeaseConflict
InvalidWindow = mod.InvalidWindow


class FakeClock:
    def __init__(self):self.now = 100.0
    def __call__(self):return self.now
    def advance(self, seconds):self.now += seconds


WAV = b'RIFF' + b'W' * 2400
WAV_OTHER = b'RIFF' + b'Y' * 2400


def descriptor(window_id, blob=WAV, force_mixed=False):
    return {'window_id':window_id, 'sha256':sha256(blob).hexdigest(), 'force_mixed':force_mixed}


class CoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.clock=FakeClock()
        self.engine=C(clock=self.clock)

    def test_freeze_forbids_old_learning_and_only_exact_kept_clip_can_drain(self):
        old=self.engine.open_capture()
        ticket=self.engine.admit(old,'w1',WAV)
        self.assertTrue(self.engine.permitted(ticket))
        freeze=self.engine.freeze(old)
        self.assertTrue(freeze['frozen'])
        self.assertFalse(self.engine.permitted(ticket))
        self.assertFalse(self.engine.complete(ticket),'late transcript may not commit')
        with self.assertRaises(LeaseConflict):self.engine.admit(old,'w1',WAV)
        drain=self.engine.start_drain(old,[descriptor('w1')])
        self.assertNotEqual(drain,old)
        with self.assertRaises(LeaseConflict):self.engine.admit(old,'w1',WAV)
        with self.assertRaises(InvalidWindow):self.engine.admit(drain,'w1',WAV_OTHER)
        with self.assertRaises(InvalidWindow):self.engine.admit(drain,'w2',WAV)
        admitted=self.engine.admit(drain,'w1',WAV)
        self.assertTrue(admitted.draining)
        self.assertTrue(self.engine.permitted(admitted))
        self.assertTrue(self.engine.complete(admitted))
        self.assertFalse(self.engine.permitted(admitted))
        with self.assertRaises(InvalidWindow):self.engine.admit(drain,'w1',WAV)
        self.assertTrue(self.engine.close(drain))
        self.assertFalse(self.engine.close(old))

    def test_drop_and_selective_keep_mixed_veto(self):
        old=self.engine.open_capture()
        self.engine.freeze(old)
        drain=self.engine.start_drain(old,[descriptor('w3',force_mixed=True),descriptor('w4',WAV_OTHER)])
        with self.assertRaises(InvalidWindow):self.engine.admit(drain,'w3',WAV,force_mixed=False)
        t=self.engine.admit(drain,'w3',WAV,force_mixed=True)
        self.assertTrue(t.force_mixed)
        self.assertTrue(self.engine.complete(t))
        self.assertEqual(self.engine.state()['queuedDrain'],1)
        failed=self.engine.admit(drain,'w4',WAV_OTHER)
        self.assertTrue(self.engine.reject(failed))
        self.assertEqual(self.engine.state()['inflightDrain'],0)
        with self.assertRaises(InvalidWindow):self.engine.admit(drain,'w4',WAV_OTHER)

    def test_expiry_frozen_and_drain(self):
        t=self.engine.open_capture()
        self.engine.freeze(t)
        self.clock.advance(89)
        self.assertEqual(self.engine.state()['mode'],'frozen')
        self.clock.advance(1)
        self.assertFalse(self.engine.state()['occupied'])
        with self.assertRaises(LeaseConflict):self.engine.start_drain(t,[descriptor('w1')])
        second=self.engine.open_capture()
        self.engine.freeze(second)
        drain=self.engine.start_drain(second,[descriptor('w2')])
        self.clock.advance(120)
        self.assertFalse(self.engine.state()['occupied'])
        with self.assertRaises(LeaseConflict):self.engine.admit(drain,'w2',WAV)

    def test_takeover_revokes_old_lease_and_old_frozen_token(self):
        a=self.engine.open_capture()
        with self.assertRaises(LeaseConflict):self.engine.open_capture()
        b=self.engine.open_capture(takeover=True)
        self.assertNotEqual(a,b)
        self.assertFalse(self.engine.close(a))
        with self.assertRaises(LeaseConflict):self.engine.freeze(a)
        self.engine.freeze(b)
        c=self.engine.open_capture(takeover=True)
        with self.assertRaises(LeaseConflict):self.engine.start_drain(b,[descriptor('w1')])
        self.assertEqual(self.engine.state()['mode'],'live')
        self.assertTrue(self.engine.close(c))

    def test_invalid_descriptors_rejected_without_consuming_frozen_lease(self):
        token=self.engine.open_capture()
        self.engine.freeze(token)
        for wrong in [[],[{}],[descriptor('w')]*2,
                      [dict(descriptor('w1'),force_mixed='yes')],
                      [dict(descriptor('w1'),sha256='abc')],
                      [descriptor('@bad')],
                      [descriptor('w'+str(i)) for i in range(5)]]:
            with self.subTest(wrong=wrong), self.assertRaises(InvalidWindow):
                self.engine.start_drain(token,wrong)
            self.assertEqual(self.engine.state()['mode'],'frozen')
        self.assertTrue(self.engine.start_drain(token,[descriptor('last')]))

    def test_explicit_discard_and_zero_leak_status(self):
        capture=self.engine.open_capture()
        self.engine.freeze(capture)
        drain=self.engine.start_drain(capture,[descriptor('key')])
        stat=self.engine.state()
        self.assertNotIn('sha256',repr(stat).lower())
        self.assertNotIn('capture',repr(stat).lower())
        self.assertNotIn(drain,repr(stat))
        self.assertTrue(self.engine.close(drain))
        self.assertFalse(self.engine.state()['occupied'])
        self.engine.drop_all()
        self.assertFalse(self.engine.state()['occupied'])

    def test_atomic_voice_update_never_runs_after_freeze(self):
        token=self.engine.open_capture()
        ticket=self.engine.admit(token,'w1',WAV)
        self.engine.freeze(token)
        learned=[]
        assert not self.engine.atomic_commit(ticket, lambda:learned.append('Dale'))
        self.assertEqual(learned,[])
        drain=self.engine.start_drain(token,[descriptor('w1',force_mixed=True)])
        new=self.engine.admit(drain,'w1',WAV,force_mixed=True)
        self.assertTrue(self.engine.atomic_commit(new,lambda:learned.append('Mixed (no training)')))
        self.assertEqual(learned,['Mixed (no training)'])
        self.assertFalse(self.engine.atomic_commit(new,lambda:learned.append('replay')))

    def test_duplicate_live_window_and_stale_nonce_rejected(self):
        token=self.engine.open_capture()
        first=self.engine.admit(token,'w1',WAV)
        with self.assertRaises(InvalidWindow):self.engine.admit(token,'w1',WAV)
        self.assertTrue(self.engine.complete(first))
        with self.assertRaises(InvalidWindow):self.engine.admit(token,'w1',WAV)
        self.assertFalse(self.engine.permitted(first))
        self.assertFalse(self.engine.complete(first))

    def test_concurrent_freeze_rejects_inflight_commit(self):
        capture=self.engine.open_capture()
        accepted=threading.Event()
        released=threading.Event()
        result=[]
        def worker():
            t=self.engine.admit(capture,'w1',WAV)
            accepted.set()
            self.assertTrue(released.wait(2))
            result.append(self.engine.complete(t))
        thread=threading.Thread(target=worker)
        thread.start()
        self.assertTrue(accepted.wait(2))
        self.engine.freeze(capture)
        released.set();thread.join(3)
        self.assertEqual(result,[False]);self.assertFalse(thread.is_alive())


if __name__ == '__main__':
    unittest.main(verbosity=2)
