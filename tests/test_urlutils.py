from apicall.urlutils import concat_urls


class TestConcatUrls:
    def test_url_and_relative_path(self):
        assert concat_urls(
            endpoints=('http://example.com:8000/api/v1', ),
            url='users',
            queries=tuple(),
        ) == ('http://example.com:8000/api/v1/users', )

    def test_domain_and_path(self):
        assert concat_urls(
            endpoints=('http://example.com', ),
            url='api/v1/users',
            queries=tuple()) == ('http://example.com/api/v1/users', )

    def test_use_https(self):
        assert concat_urls(
            endpoints=('https://example.com', ),
            url='api/v1/users',
            queries=tuple()) == ('https://example.com/api/v1/users', )

    def test_use_abs_url(self):
        assert concat_urls(
            endpoints=('http://example.com:8000', ),
            url='https://localhost:3333',
            queries=tuple(),
        ) == ('https://localhost:3333', )
