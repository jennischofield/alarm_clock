from alarm_clock import get_covid, get_weather, get_headlines, news_articles

def test_external():
    """this tests whether or not the api functions correctly gather the data"""
    get_headlines()
    assert isinstance(get_covid(),dict)
    assert isinstance(get_weather(), dict)
    assert len(news_articles) != 0
