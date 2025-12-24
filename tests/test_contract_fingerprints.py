import config.contracts as contracts


def test_contract_report_is_stable():
    """
    If this fails, you changed an evaluation contract.

    Update the expected hashes *and* document the change (why it is acceptable).
    """
    report = contracts.contract_report()

    # NOTE: These are expected to change only when you intentionally change:
    # - prompt templates / stop sequences / few-shot settings
    # - sandbox limits / docker flags / image / network policy
    # - metric definitions / compute matching
    assert report == {
        "prompt.humaneval": "59b7a7958b6802f69f8696b262d5b392603ff7266ec2c6c1c1c02beb9bb0a294",
        "prompt.mbpp": "d85d332cd704a6290562161cf5161b14321aa1fff226424d8227dc033f1aa941",
        "sandbox.default": "09c9e59391defab686c49e6d7c1a7e9d66b5beeb1d990b1b45061b15805a7eee",
        "protocol.default": "5549a1ae4a72b890671ab50ff60fdb575c76c8946fff2d6e2ca8c7aa4959d8d1",
    }


