"""Static report tests only; no private dataset or model operations."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from verify_publication import ROOT, verify, validate_metrics, validate_report, check_png, privacy


class Publication(unittest.TestCase):
    def setUp(self):
        self.m = json.loads((ROOT / 'RESULTS.json').read_text())
        self.report = (ROOT / 'README.md').read_text()

    def test_complete_public_package(self):
        self.assertEqual(verify()['status'], 'G5_STATIC_CHECK_PASS')

    def test_control_aggregates_and_paired_arithmetic(self):
        validate_metrics(self.m)
        self.assertEqual((11 - 1) / 40 * 100, 25)

    def test_report_tables_match_public_aggregates(self):
        validate_report(self.report, self.m)

    def test_inflated_tuned_score_rejected(self):
        bad = copy.deepcopy(self.m); bad['strict_40']['TunedBest']['correct'] = 40
        with self.assertRaisesRegex(ValueError, 'STRICT_METRICS'): validate_metrics(bad)

    def test_shape_success_not_content_success(self):
        bad = copy.deepcopy(self.m); bad['strict_40']['TunedBest']['FORMAT'] = 8
        with self.assertRaises(ValueError): validate_metrics(bad)

    def test_secondary_review_cannot_replace_frozen_ood(self):
        bad = copy.deepcopy(self.m); bad['ood']['strict_base_correct'] = 9
        with self.assertRaisesRegex(ValueError, 'STRICT_OOD'): validate_metrics(bad)
        bad = copy.deepcopy(self.m); bad['scoring']['secondary_review_replaces_primary'] = True
        with self.assertRaises(ValueError): validate_metrics(bad)

    def test_owner_signoff_cannot_be_invented(self):
        bad = copy.deepcopy(self.m); bad['ood']['owner_adjudication'] = 'APPROVED'
        with self.assertRaisesRegex(ValueError, 'OWNER_SIGNOFF'): validate_metrics(bad)

    def test_best_late_cannot_be_presented_as_different(self):
        bad = copy.deepcopy(self.m); bad['checkpoints']['best_step'] = 100
        with self.assertRaisesRegex(ValueError, 'BEST_EQUALS_LATE'): validate_metrics(bad)

    def test_no_artificial_overfit_or_monetary_savings(self):
        for section, key, value in [('loss', 'overfit_signal', 'OBSERVED'),
                                    ('measurements', 'monetary_savings', 'PROVEN')]:
            bad = copy.deepcopy(self.m); bad[section][key] = value
            with self.assertRaises(ValueError): validate_metrics(bad)

    def test_context_denominator_and_rag_caveat(self):
        for key, value in [('n', 40), ('actual_rag', True)]:
            bad = copy.deepcopy(self.m); bad['base_facts_knowledge_only'][key] = value
            with self.assertRaisesRegex(ValueError, 'CONTEXT_NOT_RAG'): validate_metrics(bad)

    def test_removed_report_limitations_rejected(self):
        for phrase in ('**1/6 direct**', '**overfitting was NOT_OBSERVED**',
                       '**Best and Late are identical**',
                       'Owner adjudication of that strict regression remains PENDING'):
            with self.assertRaisesRegex(ValueError, 'REPORT_CAVEAT_MISSING'):
                validate_report(self.report.replace(phrase, ''), self.m)

    def test_chart_has_intact_crc_and_expected_dimensions(self):
        data = (ROOT / 'loss_curve.png').read_bytes()
        check_png(data)
        bad = bytearray(data); bad[100] ^= 1
        with self.assertRaises(ValueError): check_png(bytes(bad))

    def test_unknown_file_rejected_before_reading_it(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root / 'unexpected.bin').write_bytes(b'SYNTHETIC_SENTINEL')
            with self.assertRaisesRegex(ValueError, 'UNEXPECTED_OR_MISSING_FILE'): verify(root)

    def test_item_level_json_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'RESULTS.json').write_text(json.dumps({'raw': 'SYNTHETIC_SENTINEL'}))
            with self.assertRaisesRegex(ValueError, 'ITEM_LEVEL_DATA'): privacy(root)


if __name__ == '__main__':
    unittest.main()
