from hpcq.energy import parse_power_csv


def test_parse_power_csv_handles_units_and_plain_values():
    assert parse_power_csv("50.2 W\n70.0 W\n") == [50.2, 70.0]
    assert parse_power_csv("50.2\n") == [50.2]
