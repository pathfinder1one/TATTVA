import requests
import json
from dataclasses import dataclass
from typing import Optional


@dataclass
class TestCases:
    input: str
    expected_output: str


@dataclass
class ProblemDetails:
    problem_id: int
    title: str
    description: str
    example: str
    difficulty: str
    url: str


class LeetCodeClient:
    def __init__(self, base_url: str = "https://leetcode.com/graphql"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Riva Demo Client)"
        })

    def _post(self, query: str, variables: dict) -> dict:
        response = self.session.post(
            self.base_url,
            json={"query": query, "variables": variables},
            timeout=30
        )
        response.raise_for_status()
        return response.json()

    def get_problem_details(self, problem_id: int) -> ProblemDetails:
        query = """
        query questionData($titleSlug: String!) {
            question(titleSlug: $titleSlug) {
                questionId
                title
                questionFrontendId
                difficulty
                content
                topicTags { name slug }
                codeSnippets { lang code }
            }
        }
        """
        slug_map = {6: "zigzag-conversion"}
        title_slug = slug_map.get(problem_id, "zigzag-conversion")
        
        data = self._post(query, {"titleSlug": title_slug})
        question = data.get("data", {}).get("question", {})
        
        if not question:
            raise ValueError(f"Problem {problem_id} not found")
        
        return ProblemDetails(
            problem_id=int(question.get("questionFrontendId", problem_id)),
            title=question.get("title", ""),
            description=question.get("content", ""),
            example="",
            difficulty=question.get("difficulty", "Medium"),
            url=f"https://leetcode.com/problems/{title_slug}/"
        )

    def get_test_cases(self, problem_id: int) -> list[TestCases]:
        default_cases = [
            TestCases(input='"PAYPALISHIRING"', expected_output='"PIAAYLHSIRPG"'
        ),
        TestCases(input='"PAYPALISHIRING"', expected_output='"PINALSIGYAHRPI"'
        ),
        TestCases(input='"A"', expected_output='"A"'
        ),
        TestCases(input='', expected_output=''
        ),
        TestCases(input='A', expected_output='A'
        ),
        TestCases(input='ABCD', expected_output='ACBD'
        )
        ]
        
        return default_cases


_client: Optional[LeetCodeClient] = None


def _get_client() -> LeetCodeClient:
    global _client
    if _client is None:
        _client = LeetCodeClient()
    return _client


def get_problem_6() -> ProblemDetails:
    return _get_client().get_problem_details(6)


def get_test_cases() -> list[TestCases]:
    return _get_client().get_test_cases(6)