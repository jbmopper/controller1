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
    # - inference config (dtype, batch_size, max_new_tokens)
    assert report == {
        "prompt.humaneval": "487b2d495e731c5e625cf09fe7d291944571896741c03990c0cd658e1d42aaa5",
        "prompt.mbpp": "d85d332cd704a6290562161cf5161b14321aa1fff226424d8227dc033f1aa941",
        "sandbox.default": "09c9e59391defab686c49e6d7c1a7e9d66b5beeb1d990b1b45061b15805a7eee",
        "protocol.default": "b411c43f3edd1cddfe69079397cdf2f36d1899da0457aa8cf4a79159f131a3de",
        "inference.default": "fe0b2dd0fbee503e6d6b20008a351f9c500e0c3f3ed25d3578e2ba1612431901",
    }


