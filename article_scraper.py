"""A module for scraping articles on the internet."""
from urllib.parse import urljoin, urlsplit
import urllib.request
from urllib.robotparser import RobotFileParser

from bs4 import BeautifulSoup
import requests
import util
from w3lib.html import replace_entities


class TimeoutRobotFileParser(RobotFileParser):
    """A slightly modified RobotFileParser with timeout option."""

    def __init__(self, url='', timeout=30):
        super().__init__(url)
        self.timeout = timeout

    def read(self):
        """
        Reads the robots.txt URL and feeds it to the parser.

        This is a copy of the urllib implementation but with the
        timeout option specified.
        """
        try:
            f = urllib.request.urlopen(self.url, timeout=self.timeout)
        except urllib.error.HTTPError as err:
            if err.code in (401, 403):
                self.disallow_all = True
            elif err.code >= 400 and err.code < 500:
                self.allow_all = True
        else:
            raw = f.read()
            self.parse(raw.decode("utf-8").splitlines())


class FailedToReadError(Exception):
    """Used when some error occurs while reading the article."""

    pass


class DisallowedError(Exception):
    """Used when the robots.txt disallows us from reading the content."""

    pass


def robot_check(url: str) -> bool:
    """Check whether we're allowed to scrape this URL."""
    split_url = urlsplit(url)
    base_url = "{0.scheme}://{0.netloc}/".format(split_url)
    if split_url.netloc == '':
        return False
    robots_url = urljoin(base_url, '/robots.txt')
    parser = TimeoutRobotFileParser(robots_url)
    try:
        parser.read()
    except Exception:
        # We don't want to crash the app if we can't read
        # for whatever reason, so we handle any error here
        # and ignore that article
        return False
    return parser.can_fetch('*', url)


def get_text_content_from_article(url: str) -> str:
    """
    Get relevant article text from the specified URL.

    Args:
        url: A URL for an article to be scraped.

    Returns:
        The text data for the article

    Raises:
        DisallowedError: The robots.txt does not allow scraping.
    """
    if not robot_check(url):
        raise DisallowedError("Disallowed: {0}".format(url))
    try:
        html = requests.get(url, timeout=30).text
    except requests.exceptions.RequestException:
        raise FailedToReadError(url)
    soup = BeautifulSoup(html, "html.parser")
    text = '. '.join([p.text for p in soup.find_all('p')])
    return util.clean_text(replace_entities(text))
