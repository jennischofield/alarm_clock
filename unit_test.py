from alarm_clock import format_string, hhmm_to_seconds, is_before, datedifference


def test_alarm():
    test_string = "Testing"
    test_time = "2020-7-8T10:35"
    test_time2 = "2020-7-7T10:30"
    assert format_string(test_time) == "Set for 10:35 on 2020-7-8"
    assert hhmm_to_seconds(test_time) == 38100
    assert is_before(test_time,test_time2) == True
    assert datedifference(test_time,test_time2) == 1
