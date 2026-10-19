"""Unit checks for the evaluator, never physical-device evidence."""
import unittest
from analyze_performance import stats,pacing_failures
class PerformanceAnalysisTests(unittest.TestCase):
    def test_regular_sixty(self):
        self.assertEqual(pacing_failures(stats([1000/60]*7200)),[])
    def test_thirty_is_not_sixty(self):
        self.assertGreaterEqual(len(pacing_failures(stats([1000/30]*3600))),3)
    def test_high_average_cannot_hide_hitches(self):
        s=stats([15]*7100+[100]*100)
        self.assertGreater(s['meanFps'],59)
        self.assertIn('frames over25ms <=0.5%',pacing_failures(s))
    def test_invalid_intervals_fail(self):
        for values in [[],[0],[float('nan')],[float('inf')],[-1]]:
            with self.assertRaises(ValueError):stats(values)
if __name__=='__main__':unittest.main()
