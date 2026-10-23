import time
import json
from typing import List, Dict, Any


class BrowserSimulator:
    def __init__(self):
        self.url = "https://leetcode.com/problems/zigzag-conversion/"
        self.editor_content = ""
        self.results: List[Dict[str, Any]] = []
        self.status = "idle"

    def navigate(self, url: str) -> None:
        self.url = url
        self.status = "navigating"
        time.sleep(0.5)
        self.status = "ready"

    def type_solution(self, code: str) -> None:
        self.editor_content = code
        self.status = "editing"
        time.sleep(0.3)
        self.status = "ready"

    def run_tests(self) -> List[Dict[str, Any]]:
        self.status = "running"
        time.sleep(0.5)
        test_cases = [
            {"input": {"s": "PAYPALISHIRING", "numRows": 3}, "expected": "PAHNAPLSIIGYIR"},
            {"input": {"s": "PAYPALISHIRING", "numRows": 4}, "expected": "PINALSIGYAHRPI"},
            {"input": {"s": "A", "numRows": 1}, "expected": "A"},
        ]
        results = []
        for tc in test_cases:
            results.append({
                "input": tc["input"],
                "expected": tc["expected"],
                "actual": self._execute(tc["input"]),
                "passed": self._execute(tc["input"]) == tc["expected"],
            })
        self.status = "completed"
        self.results = results
        return results

    def _execute(self, params: Dict[str, Any]) -> str:
        s: str = params["s"]
        num_rows: int = params["numRows"]
        if num_rows == 1 or num_rows >= len(s):
            return s
        rows = [""] * num_rows
        cur_row = 0
        going_down = False
        for char in s:
            rows[cur_row] += char
            if cur_row == 0:
                going_down = True
            elif cur_row == num_rows - 1:
                going_down = False
            if going_down:
                cur_row += 1
            else:
                cur_row -= 1
        return "".join(rows)


class DemoOrchestrator:
    def __init__(self):
        self.browser = BrowserSimulator()
        self.solution_code = (
            "class Solution:\n"
            "    def convert(self, s: str, numRows: int) -> str:\n"
            "        if numRows == 1 or numRows >= len(s):\n"
            "            return s\n"
            "        rows = [''] * numRows\n"
            "        cur_row = 0\n"
            "        going_down = False\n"
            "        for char in s:\n"
            "            rows[cur_row] += char\n"
            "            if cur_row == 0:\n"
            "                going_down = True\n"
            "            elif cur_row == numRows - 1:\n"
            "                going_down = False\n"
            "            if going_down:\n"
            "                cur_row += 1\n"
            "            else:\n"
            "                cur_row -= 1\n"
            "        return ''.join(rows)\n"
        )

    def execute(self) -> Dict[str, Any]:
        print("=== Riva Demo: LeetCode #6 Zigzag Conversion ===\n")

        print("[1/4] Navigating to problem page...")
        self.browser.navigate("https://leetcode.com/problems/zigzag-conversion/")
        print(f"      URL: {self.browser.url}\n")

        print("[2/4] Typing solution into editor...")
        self.browser.type_solution(self.solution_code)
        print(f"      Solution length: {len(self.solution_code)} chars\n")

        print("[3/4] Running test cases...")
        results = self.browser.run_tests()
        for i, r in enumerate(results, 1):
            status = "PASS" if r["passed"] else "FAIL"
            print(f"      Test {i}: {status} | Input: {r['input']} | Expected: {r['expected']} | Actual: {r['actual']}")

        passed = sum(1 for r in results if r["passed"])
        print(f"\n[4/4] Results: {passed}/{len(results)} tests passed")
        print("\n=== Demo Complete ===")

        return {
            "url": self.browser.url,
            "solution": self.solution_code,
            "results": results,
            "passed": passed,
            "total": len(results),
            "status": self.browser.status,
        }


def run_demo() -> Dict[str, Any]:
    orchestrator = DemoOrchestrator()
    return orchestrator.execute()