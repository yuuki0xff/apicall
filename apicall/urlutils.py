import typing
import urllib.parse


def is_absolute_url(url) -> bool:
    u = urllib.parse.urlsplit(url, scheme='http')
    return u.netloc != ''


def escape_query(query: str) -> str:
    name, value = query.split('=', maxsplit=1)
    return urllib.parse.quote(name) + '=' + urllib.parse.quote(value)


def concat_urls(
        endpoints: typing.Tuple[str, ...],
        url: str,
        queries: typing.Tuple[str, ...],
) -> typing.Tuple[str, ...]:
    u = urllib.parse.urlsplit(url, scheme='http')
    escaped_queries = list(escape_query(q) for q in queries)
    if u.query:
        escaped_queries.insert(0, u.query)
    query_string = '&'.join(escaped_queries)

    if is_absolute_url(url):
        components = (
            # scheme
            u.scheme,
            # hostname
            u.netloc or 'localhost',
            # path
            u.path.lstrip('/'),
            # query
            query_string,
            # fragment
            '',
        )
        return urllib.parse.urlunsplit(components),

    concated_urls = []
    for endpoint in endpoints:
        e = urllib.parse.urlsplit(endpoint, scheme='http')

        components = (
            # scheme
            e.scheme,
            # hostname
            e.netloc or 'localhost',
            # path
            e.path.rstrip('/') + '/' + u.path.lstrip('/'),
            # query
            query_string,
            # fragment
            '',
        )
        concated_urls.append(urllib.parse.urlunsplit(components))

    return tuple(concated_urls)
