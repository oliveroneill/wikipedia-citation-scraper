"""Tests the main package for creating citations."""
import main
import pytest
from unittest import mock


def test_get_url_from_ref():
    expected = "http://www.example.com"
    citation = f"{{cite web|url={expected}|title=test}}"
    assert main._get_url_from_ref(citation) == expected


@pytest.mark.parametrize("test_input,expected", [
    ('Example sentence, words.<ref name="RANDALL" />', 'Example sentence, words.'),
    ('Example sentence, words.<ref name="RANDALL"/>', 'Example sentence, words.'),
    ('Example sentence, words.', 'Example sentence, words.'),
])
def test_remove_named_ref_in_sentence(test_input, expected):
    assert main._remove_named_ref_in_sentence(test_input) == expected


@pytest.mark.parametrize("test_input,expected", [
    ('Example [[Liars (band)|Liars]] test', 'Example Liars test'),
    ('Example words [[Liars]] test', 'Example words Liars test'),
    ('Example Liars test', 'Example Liars test'),
])
def test_cleanup_wiki_links(test_input, expected):
    assert main._cleanup_wiki_links(test_input) == expected


# Example wikipedia markup for testing purposes
wiki_markup = """
On 20 August 2017, Yorke and Jonny Greenwood performed a benefit concert in [[Marche|Le Marche]], Italy, following the [[August 2016 Central Italy earthquake]].<ref>{{Cite web|url=http://pitchfork.com/news/radiohead-announce-italian-earthquake-benefit-show/|title=Radiohead Announce Italian Earthquake Benefit Show {{!}} Pitchfork|website=pitchfork.com|access-date=2017-08-22}}</ref>
Radiohead collaborated with the film composer [[Hans Zimmer]] to record a new version of the ''King of Limbs'' track "Bloom" for the nature documentary series ''[[Blue Planet II]].''
The new track, "(ocean) Bloom", features new vocals by Yorke recorded alongside the [[BBC Concert Orchestra]].<ref>{{Cite web|url=http://www.telegraph.co.uk/tv/2017/09/14/radiohead-record-new-song-sir-david-attenboroughs-blue-planet/|title=The ultimate chill out song? Radiohead record new music for David Attenborough's Blue Planet 2|last=Association|first=Press|date=2017-09-14|work=The Telegraph|access-date=2017-09-14|issn=0307-1235}}</ref>
"""


def test_create_citation_set():
    expected = [
        main.Citation(
            sentence='on 20 august 2017 yorke and jonny greenwood performed a benefit concert in le marche italy following the august 2016 central italy earthquake',
            url='http://pitchfork.com/news/radiohead-announce-italian-earthquake-benefit-show/'
        ),
        main.Citation(
            sentence='the new track ocean bloom features new vocals by yorke recorded alongside the bbc concert orchestra',
            url='http://www.telegraph.co.uk/tv/2017/09/14/radiohead-record-new-song-sir-david-attenboroughs-blue-planet/'
        )
    ]
    assert main.create_citation_set(wiki_markup) == expected


def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    response = {
        'query': {
            'pages': [{
                'revisions': [{
                    'content': wiki_markup
                }]
            }]
        }
    }
    return MockResponse(response, 200)


@mock.patch('requests.get', side_effect=mocked_requests_get)
def test_get_wikipedia_article(mock_requests):
    assert main.get_wikipedia_article("Radiohead") == wiki_markup
    # TODO: tests on bad responses
