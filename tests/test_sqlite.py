from pytest import mark

from sqlite import should_record_price


@mark.parametrize(
    "current_price_input,previous_price_input,expected",
    [
        (5.26, 3, True),
        (2, 1.5, False),
        (8, 6, False),
        (23, 20, False),
        (68.26, 65, True),
    ],
)
def test_should_record_price(current_price_input, previous_price_input, expected):
    # <3: 75%, 4-6: 50%, 7-10: 40%, 11-20: 20%, 21-50: 10%, >50: 5%
    assert should_record_price(current_price_input, previous_price_input) is expected
