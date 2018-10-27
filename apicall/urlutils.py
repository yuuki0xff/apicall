import typing
import urllib.parse


def concat_urls(
        endpoints: typing.Tuple[str, ...],
        url: str,
        queries: typing.Tuple[str, ...],
) -> typing.Tuple[str, ...]:
    u = urllib.parse.urlsplit(url, scheme='http')
    url_is_abs = u.netloc != ''
    if url_is_abs:
        return (urllib.parse.urlunsplit(u), )

    escaped_queries = tuple(urllib.parse.quote(q) for q in queries)
    query_string = '&'.join((u.query, ) + escaped_queries)

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
