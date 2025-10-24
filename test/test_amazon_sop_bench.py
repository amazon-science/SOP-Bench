"""Tests for AmazonSOPBench module."""

import pytest


@pytest.mark.xfail
def test_that_you_wrote_tests():
    """Test that you wrote tests."""
    from textwrap import dedent

    assertion_string = dedent(
        """\
    No, you have not written tests.

    However, unless a test is run, the pytest execution will fail
    due to no tests or missing coverage. So, write a real test and
    then remove this!
    """
    )
    assert False, assertion_string


def test_amazon_sop_bench_importable():
    """Test amazon_sop_bench is importable."""
    import amazon_sop_bench  # noqa: F401
