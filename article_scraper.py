"""A module for scraping articles on the internet."""
from urllib.error import URLError
from urllib.parse import urljoin, urlsplit
from urllib.robotparser import RobotFileParser

from bs4 import BeautifulSoup

import requests

import util

from w3lib.html import replace_entities


class DisallowedError(Exception):
    """Used when the robots.txt disallows us from reading the content."""

    pass


def robot_check(url: str) -> bool:
    """Check whether we're allowed to scrape this URL."""
    base_url = "{0.scheme}://{0.netloc}/".format(urlsplit(url))
    robots_url = urljoin(base_url, '/robots.txt')
    parser = RobotFileParser(robots_url)
    try:
        parser.read()
    except URLError:
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
    html = requests.get(url).text
    soup = BeautifulSoup(html, "html.parser")
    text = '. '.join([p.text for p in soup.find_all('p')])
    return util.clean_text(replace_entities(text))
