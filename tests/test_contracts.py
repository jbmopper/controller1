"""
Contract Fingerprint Tests

These tests ensure that the evaluation contracts (prompts, sandbox, metrics)
don't change silently. Any modification to the evaluation setup will cause
these tests to fail, forcing an explicit acknowledgment of the change.

To update after an intentional change:
    1. Run: uv run python main.py contracts
    2. Copy the new fingerprints into EXPECTED_FINGERPRINTS below
    3. Document why the change was made in your commit message
"""

import pytest

from config.contracts import (
    contract_report,
    prompt_contract_fingerprint,
    sandbox_contract_fingerprint,
    protocol_fingerprint,
)


# Pin the current fingerprints - update these intentionally when contracts change
EXPECTED_FINGERPRINTS = {
    "prompt.humaneval": "59b7a7958b6802f69f8696b262d5b392603ff7266ec2c6c1c1c02beb9bb0a294",
    "prompt.mbpp": "d85d332cd704a6290562161cf5161b14321aa1fff226424d8227dc033f1aa941",
    "sandbox.default": "09c9e59391defab686c49e6d7c1a7e9d66b5beeb1d990b1b45061b15805a7eee",
    "protocol.default": "5549a1ae4a72b890671ab50ff60fdb575c76c8946fff2d6e2ca8c7aa4959d8d1",
}


class TestContractFingerprints:
    """Test that contract fingerprints remain stable."""

    def test_all_contracts_stable(self):
        """All contract fingerprints should match expected values."""
        actual = contract_report()
        
        mismatches = []
        for key, expected in EXPECTED_FINGERPRINTS.items():
            if actual.get(key) != expected:
                mismatches.append(
                    f"  {key}:\n"
                    f"    expected: {expected}\n"
                    f"    actual:   {actual.get(key, 'MISSING')}"
                )
        
        if mismatches:
            pytest.fail(
                "Contract fingerprint drift detected!\n"
                "If this change is intentional, update EXPECTED_FINGERPRINTS in this file.\n\n"
                + "\n".join(mismatches)
            )

    def test_humaneval_prompt_contract(self):
        """HumanEval prompt contract should be stable."""
        actual = prompt_contract_fingerprint("humaneval")
        expected = EXPECTED_FINGERPRINTS["prompt.humaneval"]
        assert actual == expected, (
            f"HumanEval prompt contract changed!\n"
            f"Expected: {expected}\n"
            f"Actual:   {actual}"
        )

    def test_mbpp_prompt_contract(self):
        """MBPP prompt contract should be stable."""
        actual = prompt_contract_fingerprint("mbpp")
        expected = EXPECTED_FINGERPRINTS["prompt.mbpp"]
        assert actual == expected, (
            f"MBPP prompt contract changed!\n"
            f"Expected: {expected}\n"
            f"Actual:   {actual}"
        )

    def test_sandbox_contract(self):
        """Sandbox contract should be stable."""
        actual = sandbox_contract_fingerprint()
        expected = EXPECTED_FINGERPRINTS["sandbox.default"]
        assert actual == expected, (
            f"Sandbox contract changed!\n"
            f"Expected: {expected}\n"
            f"Actual:   {actual}"
        )

    def test_protocol_contract(self):
        """Evaluation protocol should be stable."""
        actual = protocol_fingerprint()
        expected = EXPECTED_FINGERPRINTS["protocol.default"]
        assert actual == expected, (
            f"Evaluation protocol changed!\n"
            f"Expected: {expected}\n"
            f"Actual:   {actual}"
        )


class TestContractReportCompleteness:
    """Ensure contract_report covers all expected keys."""

    def test_report_has_all_keys(self):
        """contract_report() should include all expected fingerprints."""
        report = contract_report()
        missing = set(EXPECTED_FINGERPRINTS.keys()) - set(report.keys())
        assert not missing, f"contract_report() missing keys: {missing}"

    def test_no_unexpected_keys(self):
        """contract_report() shouldn't have keys we don't track."""
        report = contract_report()
        extra = set(report.keys()) - set(EXPECTED_FINGERPRINTS.keys())
        if extra:
            pytest.fail(
                f"contract_report() has new keys not in EXPECTED_FINGERPRINTS: {extra}\n"
                "Add these to EXPECTED_FINGERPRINTS if intentional."
            )

