import app

def test_amount_with_comma():
    assert app.clean_amount("200,000") == 200000


def test_amount_with_dot():
    assert app.clean_amount("80.000") == 80000


def test_invalid_amount_is_rejected():
    assert app.clean_amount("abc") is None


def test_date_is_normalized():
    assert app.clean_date("07/10/2026") == "2026-10-07"


def test_invalid_date_is_rejected():
    assert app.clean_date("2026-13-45") is None