"""Synthetic examples test metrics, NOT model disease accuracy."""
import importlib.util
import unittest


@unittest.skipUnless(importlib.util.find_spec('numpy'), 'NumPy not installed')
class MetricsTests(unittest.TestCase):
    def test_per_class_confusion_f1_and_reliability_are_real_computations(self):
        from ml.metrics import classification_report
        report = classification_report([0,0,1,1], [[.9,.1],[.4,.6],[.1,.9],[.2,.8]], ['a','b'])
        self.assertEqual(report['confusion_matrix'], [[1,1],[0,2]])
        self.assertEqual(report['accuracy'], .75)
        self.assertAlmostEqual(report['per_class']['a']['recall'], .5)
        self.assertGreater(report['reliability']['expected_calibration_error'], 0)

    def test_bad_scores_are_rejected_instead_of_softmax_again(self):
        from ml.metrics import classification_report
        with self.assertRaisesRegex(ValueError, 'probability vector'):
            classification_report([0], [[3.,2.]], ['a','b'])

    def test_insufficient_validation_evidence_keeps_every_result_uncertain(self):
        from ml.metrics import choose_policy, selective_report
        policy = choose_policy([0,1], [[.99,.01],[.01,.99]], min_accepted=100)
        self.assertFalse(policy['validated'])
        self.assertEqual(selective_report([0,1], [[.99,.01],[.01,.99]], policy)['accepted_count'], 0)

    def test_threshold_policy_comes_from_validation_only(self):
        from ml.metrics import choose_policy
        policy = choose_policy([0]*200, [[.99,.01]]*200, min_accepted=100)
        self.assertTrue(policy['validated'])
        self.assertEqual(policy['selection_split'], 'validation')
        self.assertIn('Not proof', policy['limitations'])


if __name__ == '__main__':
    unittest.main()
