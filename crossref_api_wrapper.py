import json
import re
import string
from typing import Optional

from habanero import Crossref
from requests.exceptions import HTTPError
from strsimpy.jaro_winkler import JaroWinkler
from strsimpy.normalized_levenshtein import NormalizedLevenshtein


class CrossrefNetworkError(Exception):
    pass


class CrossrefAPIWrapper(object):
    def __init__(self, mailto: Optional[str] = None) -> None:
        self.cr = Crossref(mailto=mailto)
        self.jaro_winkler = JaroWinkler()

    def search(
        self,
        title: str,
        author: Optional[str] = None,
        publication_type: Optional[str] = None,
        publication_year: Optional[int] = None,
    ) -> list[dict]:
        search_results = self.cr.works(
            query_bibliographic=title, query_author=author, limit=3
        )

        items = search_results.get("message", {}).get("items", [])

        if publication_type:
            items = [x for x in items if x.get("type") == publication_type]

        if publication_year:
            items = [
                x
                for x in items
                if x.get("published", {}).get("date-parts", [[None]])[0][0]
                == publication_year
            ]

        results = []
        for x in items:
            if title_candidate := self.get_title(x):
                score = self.calculate_score(
                    title, title_candidate, author, self.get_first_author(x)
                )
                if score > 40:
                    results.append({"score": score, "record": x})
        return results

    def calculate_score(
        self,
        title_a: str,
        title_b: str,
        author_a: Optional[str] = None,
        author_b: Optional[str] = None,
    ) -> int:
        normalized_levenshtein = NormalizedLevenshtein()
        distance = normalized_levenshtein.distance(
            CrossrefAPIWrapper.preprocess_string(title_a),
            CrossrefAPIWrapper.preprocess_string(title_b),
        )
        distance = round(100 - (distance * 100))
        if author_a and author_b:
            author_distance = self.jaro_winkler.similarity(
                CrossrefAPIWrapper.preprocess_string(author_a),
                CrossrefAPIWrapper.preprocess_string(author_b),
            )
            distance = 0.7 * distance + 30 * author_distance
        return int(distance)

    @staticmethod
    def preprocess_string(x: str) -> str:
        """Removes punctuation, double whitespace and converts to lowercase."""
        x = x.translate(
            str.maketrans(string.punctuation, " " * len(string.punctuation))
        )
        x = x.lower()
        x = (
            x.replace("<i>", " ")
            .replace("</i>", " ")
            .replace("<sup>", " ")
            .replace("</sup>", " ")
            .replace("&amp;quot;", " ")
            .replace("'", " ")
        )
        return re.sub(" +", " ", x).strip()

    def find_by_doi(self, doi: str) -> dict:
        try:
            result = self.cr.works(ids=doi)
        except HTTPError:
            raise CrossrefNetworkError
        return result.get("message")

    @staticmethod
    def get_first_author(item: dict) -> Optional[str]:
        if authors := item.get("author"):
            first_author = authors[0].get("family")
            if not first_author:
                first_author = authors[0].get("given", "").split(" ")[-1]
            return first_author
        return None

    @staticmethod
    def get_title(item: dict) -> Optional[str]:
        title = item.get("title")
        if title:
            return title[0]
        return None
