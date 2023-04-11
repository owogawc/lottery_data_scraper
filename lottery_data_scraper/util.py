import base64
import os
import requests
from tempfile import gettempdir

def fetch_html(url):
    """
    Helper to fetch and cache html responses.

    During development and while testing, we'll be hitting the same urls often.
    The content of the pages probably won't be changing.
    Caching the results will speed up development,
    and the servers will appreciate us for not spamming requests.

    The responses are cached in the operating systems tempfile directory.
    That's probably /tmp/ or /var/tmp/ on Unix flavors and C:/temp/ on Windows.
    The filename is based on the URL. But since the URL might contain
    characters that are invalid for filenames, we base64 encode the URL.
    """
    safe_filename = base64.urlsafe_b64encode(bytes(url, "utf-8")).decode("utf-8")
    filepath = os.path.join(gettempdir(), safe_filename)

    if os.path.isfile(filepath) and os.environ.get("USE_CACHE", False):
        with open(filepath, "r") as f:
            return f.read()
    else:
        # We are relying on the outside world when we make a request, so we
        # might want to wrap this in a try/except. But we'd
        # only want to do that in two cases.
        #
        # 1. We have a way of handling exceptions,
        # A good example would be to catch exceptions and retry the
        # request; maybe the network was down.
        #
        # 2. We can't handle the exception, but we want to log something
        # more useful than the stack trace that will get spit out if
        # we just let the exception go uncaught.
        #
        # In this case, I don't think it's worth muddying up the code
        # trying to handle exceptions here. It's easy enough to just re-run
        # the script.
        html = requests.get(url).text
        if os.environ.get("USE_CACHE", False):
            with open(filepath, "w+") as f:
                f.write(html)
        return html
