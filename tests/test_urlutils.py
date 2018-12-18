from apicall.urlutils import is_absolute_url, escape_query, concat_urls


class TestIsAbsoluteUrl:
    def test_missing_schema(self):
        assert is_absolute_url('//localhost/path')

    def test_missing_hostname(self):
        assert not is_absolute_url('/path-only')

    def test_relative_path(self):
        assert not is_absolute_url('get')


class TestEscapeQuery:
    def test_normal(self):
        assert escape_query('name=value') == 'name=value'

    def test_escape_key(self):
        assert escape_query('a b=value') == 'a%20b=value'

    def test_escape_value(self):
        assert escape_query('name=a b') == 'name=a%20b'


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
