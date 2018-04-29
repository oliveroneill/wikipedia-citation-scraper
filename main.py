"""A script for generating a citation list for a wikipedia article."""
import argparse
import json
import re

import article_scraper

import requests

import typing

import util

API_URL = 'https://en.wikipedia.org/w/api.php'

"""
Citation is a namedtuple representing a sentence and its source.

Args:
    sentence: A sentence in a wikipedia article.
    url: The source of information that produced the sentence.
"""
Citation = typing.NamedTuple("Citation", [('sentence', str), ('url', str)])


"""
ArticleSummary is a namedtuple representing a sentence and the content its
summarised from.

Args:
    sentence: A sentence in a wikipedia article.
    url: The article content the sentence was derived from.
"""
ArticleSummary = typing.NamedTuple("ArticleSummary", [('sentence', str), ('source', str)])


def _cleanup_wiki_links(sentence: str) -> str:
    # Remove nowiki tags
    sentence = sentence.replace('<nowiki/>', '')
    # Replace links with its name "[[Liars (band)|Liars]]" -> "Liars"
    sentence = re.sub(r'\[\[[^\]]+\|([^\]]+)+\]\]', r'\1', sentence)
    # Replace links with its name "[[Liars]]" -> "Liars"
    return re.sub(r'\[\[([^\|]+?)\]\]', r'\1', sentence)


def _remove_named_ref_in_sentence(sentence: str) -> str:
    # Remove named refs
    regex = r'<ref name="[\s\S]+"\s*\/>'
    if re.compile(regex).search(sentence):
        # "sentence<ref name="RANDALL" />" -> "sentence"
        sentence, *_ = re.split(regex, sentence)
    return sentence


def _get_url_from_ref(ref: str) -> str:
    # {{cite web|url=http://www.example.com|title=test}} -> http://www.example.com
    # This assumes input as specified above, it will error if it does not
    # receive the correct format
    _, url, *_ = ref.split("|url=")
    url, *_ = re.split(r"(\||\})", url)
    url, *_ = re.split(r"(\[\[\|\]\])", url)
    return url


def create_citation_set(wiki_markup: str) -> [Citation]:
    """
    Get a list of citations from wikipedia markup.

    This will ignore named refs (for now).
    """
    rtn = []
    # Find all sentence that end in a ref tag
    for cited_sentence in re.findall('(.*?<\/ref>)', wiki_markup):
        # split by line
        for para in cited_sentence.split("\n"):
            # remove refs that don't specify a url
            para = _remove_named_ref_in_sentence(para)
            # remove paragraphs that don't contain refs
            if "<ref>" not in para:
                continue
            # parse the ref
            sentence, ref, *_ = para.split("<ref>")
            if "|url=" not in ref:
                continue
            url = _get_url_from_ref(ref)
            # Cleanup the sentence
            clean_sentence = _cleanup_wiki_links(sentence=sentence)
            clean_sentence = util.clean_text(text=clean_sentence)
            if len(clean_sentence) > 0:
                rtn.append(Citation(url=url, sentence=clean_sentence))
    return rtn


def get_wikipedia_article(title: str) -> str:
    """
    Get wiki markup from a title.

    Args:
        title: A wikipedia article title.

    Returns:
        The wikipedia markup text for the input article

    Raises:
        ValueError: The wikipedia API did not respond with the expected data
    """
    # Query based on title
    params = {
        'action': 'query',
        'titles': title,
        'prop': 'revisions',
        'rvprop': 'content',
        'format': 'json',
        'formatversion': 2
    }
    r = requests.get(API_URL, params=params)
    # Parse JSON response
    try:
        response = r.json()
    except ValueError:
        raise ValueError("Unexpected response")
    # Safety around checking response
    if "query" not in response:
        raise ValueError("Unexpected response. Missing query")
    # Get the content
    return response["query"]["pages"][0]["revisions"][0]["content"]


def create_article_summary_set(citations: [Citation]) -> [ArticleSummary]:
    """Create a list of summaries and their original article content."""
    summaries = []
    for c in citations:
        print("Reading", c.url)
        try:
            source = article_scraper.get_text_content_from_article(c.url)
            summary = ArticleSummary(sentence=c.sentence, source=source)
            summaries.append(summary)
        except (article_scraper.DisallowedError, article_scraper.FailedToReadError):
            pass
    return summaries


def main(title: str):
    """
    Get a list of citations from a wikipedia article with the given title.

    Args:
        title: A wikipedia article title.

    Raises:
        ValueError: The wikipedia API did not respond with the expected data
    """
    wiki_markup = get_wikipedia_article(title=title)
    citations = create_citation_set(wiki_markup=wiki_markup)
    data = create_article_summary_set(citations)
    json_output = json.dumps([d._asdict() for d in data])
    with open("{}.json".format(title), "w") as file:
        file.write(json_output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Parse wikipedia articles to retrieve citations.'
    )
    parser.add_argument('title', type=str, help='Wikipedia title')
    args = parser.parse_args()

    main(title=args.title)
