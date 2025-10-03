"""RefactorElf - Keeps code simple and clean"""
from agents.base_agent import BaseAgent
from typing import Dict, Any

class RefactorElf(BaseAgent):
    """Simplifies code that gets too complex"""

    def __init__(self, llm_client=None):
        super().__init__("RefactorElf", None, llm_client)
        self.vibe = "minimalist"
        self.complexity_limit = 50  # Lines per function
        self.file_limit = 200  # Lines per file

    def get_prompt(self, context: Dict[str, Any]) -> str:
        return f"""
        You are RefactorElf, the simplifier.

        Code to review: {context.get('code', 'none')}
        Issue: {context.get('issue', 'too complex')}

        How to simplify? Options:
        - SPLIT: Break into multiple functions
        - EXTRACT: Pull out to separate file
        - SIMPLIFY: Rewrite more simply
        - FINE: It's actually okay as is

        Suggest the action and how to do it.
        """

    def scan_complexity(self, file_path: str) -> Dict[str, Any]:
        """Scan a file for complexity issues"""
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()

            issues = []

            # Check file length
            if len(lines) > self.file_limit:
                issues.append({
                    "type": "file_too_long",
                    "lines": len(lines),
                    "suggestion": "Split into multiple files"
                })

            # Find functions (simple detection)
            function_starts = []
            for i, line in enumerate(lines):
                if line.strip().startswith('def '):
                    function_starts.append(i)

            # Check function lengths
            for i, start in enumerate(function_starts):
                end = function_starts[i + 1] if i + 1 < len(function_starts) else len(lines)
                function_length = end - start

                if function_length > self.complexity_limit:
                    function_name = lines[start].split('def ')[1].split('(')[0]
                    issues.append({
                        "type": "function_too_long",
                        "function": function_name,
                        "lines": function_length,
                        "suggestion": "Break into smaller functions"
                    })

            return {
                "file": file_path,
                "issues": issues,
                "needs_refactoring": len(issues) > 0
            }
        except Exception as e:
            return {"error": str(e)}

    def suggest_split(self, function_code: str) -> Dict[str, Any]:
        """Suggest how to split a function"""
        context = {
            "code": function_code,
            "issue": "function too long",
            "question": "How to split this into smaller functions?"
        }
        return self.think(context)

    def simplify_code(self, code: str) -> Dict[str, Any]:
        """Suggest simpler version of code"""
        context = {
            "code": code,
            "issue": "too complex",
            "question": "How to make this simpler?"
        }
        return self.think(context)

class ComplexityScanner(BaseAgent):
    """Sub-agent that finds complex code"""

    def __init__(self, llm_client=None):
        super().__init__("ComplexityScanner", None, llm_client)
        self.vibe = "detective"

    def get_prompt(self, context: Dict[str, Any]) -> str:
        return f"""
        Find complexity in this code.

        Code: {context.get('code')}

        Look for:
        - Nested loops (bad)
        - Long functions (over 30 lines)
        - Too many parameters (over 5)
        - Deep nesting (over 3 levels)
        - Duplicate code

        What's the biggest issue?
        """

class Splitter(BaseAgent):
    """Sub-agent that suggests how to split code"""

    def __init__(self, llm_client=None):
        super().__init__("Splitter", None, llm_client)
        self.vibe = "surgical"

    def get_prompt(self, context: Dict[str, Any]) -> str:
        return f"""
        Split this code into smaller pieces.

        Code: {context.get('code')}
        Current length: {context.get('lines')} lines

        Suggest splits:
        - Function names for each piece
        - What each piece does
        - Keep each under 30 lines
        """