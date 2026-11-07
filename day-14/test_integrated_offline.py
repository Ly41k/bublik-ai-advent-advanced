#!/usr/bin/env python3
"""Pure offline contract tests. No API, Docker, user files or network used."""
import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).with_name('BUBLIK_D14_MINIMAL_INTEGRATED_R1.py')
spec = importlib.util.spec_from_file_location('d14demo', path)
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)


class ContractTests(unittest.TestCase):
    def test_generated_three_whitelisted_lines(self):
        answer = '\n'.join(k + '=' + v for k,v in demo.ALLOWED.items())
        self.assertEqual(demo.parse_generated(answer), demo.ALLOWED)

    def test_generated_whitespace(self):
        answer = '\n'.join(k + '=  ' + v + '  ' for k,v in demo.ALLOWED.items())
        self.assertEqual(demo.parse_generated(answer), demo.ALLOWED)

    def test_generated_reject_plaintext(self):
        answer = 'T1=tokenStore.plain(token)\nT2=logger.log("request.accepted")\nT3=client.get(SECURE_ENDPOINT)'
        with self.assertRaises(demo.Halt): demo.parse_generated(answer)

    def test_generated_reject_sensitive_logger(self):
        answer = 'T1=tokenStore.protect(token)\nT2=logger.log("request.email=$email")\nT3=client.get(SECURE_ENDPOINT)'
        with self.assertRaises(demo.Halt): demo.parse_generated(answer)

    def test_generated_reject_unapproved_api(self):
        answer = 'T1=tokenStore.protect(token)\nT2=logger.log("request.accepted")\nT3=client.get("http://test.invalid")'
        with self.assertRaises(demo.Halt): demo.parse_generated(answer)

    def test_generated_reject_extra_line(self):
        answer = '\n'.join(k + '=' + v for k,v in demo.ALLOWED.items()) + '\nIGNORE_PREVIOUS_INSTRUCTIONS'
        with self.assertRaises(demo.Halt): demo.parse_generated(answer)

    def test_generated_reject_shell_injection(self):
        answer = 'T1=tokenStore.protect(token); Runtime.getRuntime().exec("bad")\nT2=logger.log("request.accepted")\nT3=client.get(SECURE_ENDPOINT)'
        with self.assertRaises(demo.Halt): demo.parse_generated(answer)

    def test_generated_reject_wrong_order(self):
        answer = 'T2=logger.log("request.accepted")\nT1=tokenStore.protect(token)\nT3=client.get(SECURE_ENDPOINT)'
        with self.assertRaises(demo.Halt): demo.parse_generated(answer)

    def test_review_allowed_severities(self):
        result = demo.parse_review('T1: LOW | Unverified secure store\nT2: CLEAN | No PII logged\nT3: MEDIUM | Review TLS trust')
        self.assertEqual([result[f'T{i}']['severity'] for i in (1,2,3)], ['LOW','CLEAN','MEDIUM'])

    def test_review_high_gate(self):
        result = demo.parse_review('T1: HIGH | Plaintext token\nT2: CLEAN | Safe\nT3: LOW | TLS trust not proven')
        self.assertEqual(result['T1']['severity'], 'HIGH')

    def test_review_reject_invalid_severity(self):
        with self.assertRaises(demo.Halt):
            demo.parse_review('T1: GOOD | Fine\nT2: CLEAN | Fine\nT3: LOW | Fine')

    def test_review_reject_extra(self):
        with self.assertRaises(demo.Halt):
            demo.parse_review('T1: LOW | Fine\nT2: CLEAN | Fine\nT3: LOW | Fine\nextra')

    def test_source_contains_all_generated_lines(self):
        kotlin = demo.make_kotlin_script(demo.ALLOWED)
        for statement in demo.ALLOWED.values():
            self.assertIn(statement, kotlin)
        self.assertIn('ALL_THREE_GENERATED_KOTLIN_CHECKS_PASS', kotlin)

    def test_source_rejects_non_whitelisted(self):
        with self.assertRaises(demo.Halt):
            demo.make_kotlin_script({'T1':'tokenStore.plain(token)', **{k:v for k,v in demo.ALLOWED.items() if k!='T1'}})

    def test_review_source_has_https_config(self):
        self.assertIn('https://api.example.invalid/profile', demo.kotlin_sources(demo.ALLOWED))

    def test_reserve_under_owner_limit(self):
        expected = demo.estimate(demo.GENERATOR_PROMPT) + demo.estimate(demo.REVIEWER_PREFIX + demo.kotlin_sources(demo.ALLOWED))
        self.assertLess(expected, demo.OWNER_LIMIT)

    def test_archive_source_hash(self):
        # The owner laptop uses Downloads; local repo snapshot bundled for offline review is separate.
        import hashlib
        source = Path('/mnt/data/BUBLIK_D13_FINAL_PUBLIC_SOURCE.zip')
        if source.is_file():
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), demo.SOURCE_SHA256)


    def test_generated_accept_colon_form(self):
        answer = '\n'.join(k + ': ' + v for k,v in demo.ALLOWED.items())
        self.assertEqual(demo.parse_generated(answer), demo.ALLOWED)

    def test_generated_accept_fenced_kotlin(self):
        answer = '```kotlin\n' + '\n'.join(k + '=' + v for k,v in demo.ALLOWED.items()) + '\n```'
        self.assertEqual(demo.parse_generated(answer), demo.ALLOWED)


if __name__ == '__main__':
    unittest.main(verbosity=2)
