"""StructureBot - Maintains file organization"""
from agents.base_agent import BaseAgent
from typing import Dict, Any, List
import os

class StructureBot(BaseAgent):
    """Keeps the codebase organized"""

    def __init__(self, llm_client=None):
        super().__init__("StructureBot", None, llm_client)
        self.vibe = "organized"
        self.project_root = "/Users/mdawson/Dawson/DawsOSB/dawsos"

    def get_prompt(self, context: Dict[str, Any]) -> str:
        return f"""
        You are StructureBot, the file organizer.

        New functionality: {context.get('functionality', 'unknown')}
        Current structure:
        - agents/ (agent implementations)
        - capabilities/ (external data integrations)
        - core/ (graph and system logic)
        - workflows/ (patterns and workflows)
        - storage/ (data persistence)
        - ui/ (user interface)
        - prompts/ (agent prompts)

        Where should this live? Return:
        - folder: which folder
        - filename: suggested filename.py
        - reason: why there (one sentence)
        """

    def find_home(self, functionality: str) -> Dict[str, Any]:
        """Find where new functionality should live"""
        context = {"functionality": functionality}
        response = self.think(context)

        # Create the file path
        if response.get('folder') and response.get('filename'):
            file_path = os.path.join(
                self.project_root,
                response['folder'],
                response['filename']
            )
            response['full_path'] = file_path

        return response

    def suggest_refactor(self, file_path: str, line_count: int) -> Dict[str, Any]:
        """Suggest how to refactor a large file"""
        context = {
            "file_path": file_path,
            "line_count": line_count,
            "question": "Should we split this file?"
        }
        return self.think(context)

    def scan_structure(self) -> Dict[str, Any]:
        """Scan project structure and suggest improvements"""
        structure = self._get_project_structure()

        context = {
            "structure": structure,
            "question": "Any organization improvements needed?"
        }
        return self.think(context)

    def _get_project_structure(self) -> Dict[str, List[str]]:
        """Get current project structure"""
        structure = {}

        for root, dirs, files in os.walk(self.project_root):
            # Skip hidden and cache directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']

            rel_path = os.path.relpath(root, self.project_root)
            if rel_path == '.':
                rel_path = 'root'

            structure[rel_path] = files

        return structure

class FileCreator(BaseAgent):
    """Sub-agent that creates new files with boilerplate"""

    def __init__(self, llm_client=None):
        super().__init__("FileCreator", None, llm_client)
        self.vibe = "creative"

    def get_prompt(self, context: Dict[str, Any]) -> str:
        return f"""
        Create boilerplate for a new file.

        File type: {context.get('file_type', 'python')}
        Purpose: {context.get('purpose', 'unknown')}
        Filename: {context.get('filename', 'new_file.py')}

        Return minimal boilerplate code to get started.
        Include:
        - File docstring
        - Basic imports
        - Main class or function structure
        - Keep it under 20 lines
        """

class FolderOrganizer(BaseAgent):
    """Sub-agent that suggests folder organization"""

    def __init__(self, llm_client=None):
        super().__init__("FolderOrganizer", None, llm_client)
        self.vibe = "systematic"

    def get_prompt(self, context: Dict[str, Any]) -> str:
        return f"""
        Suggest folder organization.

        Current folders: {context.get('folders', [])}
        New items to organize: {context.get('new_items', [])}

        Where should each item go? Be consistent with existing patterns.
        """