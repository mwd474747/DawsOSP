"""CodeMonkey - The agent that writes actual code"""
from agents.base_agent import BaseAgent
from typing import Dict, Any
import os
import logging

logger = logging.getLogger(__name__)

class CodeMonkey(BaseAgent):
    """Simple code writer - keeps everything simple"""

    def __init__(self, graph=None, llm_client=None):
        super().__init__("CodeMonkey", graph, llm_client)
        self.vibe = "eager to code"
        self.max_lines = 50  # Keep it simple!

    def get_prompt(self, context: Dict[str, Any]) -> str:
        return f"""
        You are CodeMonkey, a simple code writer.

        Task: {context.get('task', 'write code')}
        File: {context.get('file_path', 'unknown')}
        Language: {context.get('language', 'python')}

        Rules:
        - Keep it under {self.max_lines} lines
        - Make it work first, optimize never
        - Use simple variable names
        - Add minimal comments
        - No complex abstractions
        - If it's getting complex, just make it work

        Write the code:
        """

    def write_function(self, function_name: str, purpose: str, file_path: str) -> Dict[str, Any]:
        """Write a single function"""
        context = {
            "task": f"Write a function called {function_name} that {purpose}",
            "file_path": file_path,
            "language": "python"
        }

        response = self.think(context)

        # Actually write the file (in real implementation)
        if response.get('code'):
            self._write_to_file(file_path, response['code'])

        return response

    def fix_bug(self, file_path: str, bug_description: str) -> Dict[str, Any]:
        """Fix a bug in existing code"""
        # Read current code
        current_code = self._read_file(file_path)

        context = {
            "task": f"Fix this bug: {bug_description}",
            "current_code": current_code,
            "file_path": file_path
        }

        return self.think(context)

    def simplify(self, file_path: str, function_name: str) -> Dict[str, Any]:
        """Simplify a complex function"""
        current_code = self._read_file(file_path)

        context = {
            "task": f"Simplify the {function_name} function - break it into smaller pieces",
            "current_code": current_code,
            "file_path": file_path
        }

        return self.think(context)

    def _write_to_file(self, file_path: str, content: str):
        """Actually write code to file"""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error writing file: {e}")
            return False

    def _read_file(self, file_path: str) -> str:
        """Read existing file"""
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            logger.debug(f"File not found: {file_path}, returning empty string")
            return ""
        except PermissionError as e:
            logger.warning(f"Permission denied reading {file_path}: {e}")
            return ""
        except Exception as e:
            logger.error(f"Unexpected error reading {file_path}: {e}", exc_info=True)
            return ""

class FunctionWriter(BaseAgent):
    """Sub-agent that writes individual functions"""

    def __init__(self, graph=None, llm_client=None):
        super().__init__("FunctionWriter", graph, llm_client)
        self.vibe = "focused"

    def get_prompt(self, context: Dict[str, Any]) -> str:
        return f"""
        Write ONLY a single function.

        Function name: {context.get('name')}
        Purpose: {context.get('purpose')}
        Parameters: {context.get('params', 'decide yourself')}
        Returns: {context.get('returns', 'decide yourself')}

        Just the function, nothing else. Make it simple and working.
        """

class ImportManager(BaseAgent):
    """Sub-agent that manages imports"""

    def __init__(self, graph=None, llm_client=None):
        super().__init__("ImportManager", graph, llm_client)
        self.vibe = "organized"

    def get_prompt(self, context: Dict[str, Any]) -> str:
        return f"""
        What imports are needed?

        Code: {context.get('code')}
        Current imports: {context.get('current_imports', [])}

        Return just the import lines needed, one per line.
        Only standard library and common packages.
        """

class DocStringBot(BaseAgent):
    """Sub-agent that adds simple docstrings"""

    def __init__(self, graph=None, llm_client=None):
        super().__init__("DocStringBot", graph, llm_client)
        self.vibe = "helpful"

    def get_prompt(self, context: Dict[str, Any]) -> str:
        return f"""
        Add a simple one-line docstring.

        Function: {context.get('function_code')}

        Return just the docstring text (will be added as '''docstring''').
        Keep it under 10 words.
        """