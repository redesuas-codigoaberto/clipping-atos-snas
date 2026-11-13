"""Download pages from the Diário Oficial site, retrying the failures that are usually transient."""

import time
import urllib.error
import urllib.request

HEADERS = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
ATTEMPTS = 4
TIMEOUT = 45
RETRY_STATUSES = (429, 500, 502, 503, 504)
# Upper bound for a server-sent Retry-After, so one answer cannot stall the daily run.
MAX_RETRY_AFTER = 120


def retry_delay(attempt, retry_after=None):
    """Seconds to wait before the next attempt: the server's Retry-After, else 5, 10, 15... seconds."""
    try:
        requested = min(int(retry_after or 0), MAX_RETRY_AFTER)
    except ValueError:
        # Retry-After may also be an HTTP date; fall back to the linear backoff.
        requested = 0
    return requested or 5 * (attempt + 1)


def get_html(url, sleep=time.sleep):
    """The page at `url` decoded as UTF-8.

    HTTP 429 and 5xx answers, timeouts and network errors are retried; other HTTP errors are raised at once.
    """
    request = urllib.request.Request(url, headers=HEADERS)
    for attempt in range(ATTEMPTS):
        last = attempt == ATTEMPTS - 1
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                return response.read().decode('utf-8')
        # HTTPError is a subclass of OSError, so it must be handled first.
        except urllib.error.HTTPError as exc:
            if exc.code not in RETRY_STATUSES or last:
                raise
            sleep(retry_delay(attempt, exc.headers.get('Retry-After')))
        except (TimeoutError, OSError):
            if last:
                raise
            sleep(retry_delay(attempt))
    raise AssertionError('unreachable')
