"""StructureBot - Maintains file organization

Phase 3.1: Added comprehensive type hints for better type safety.
"""
from agents.base_agent import BaseAgent
from typing import Dict, Any, List, Optional, TypeAlias
import os

# Type aliases for clarity
ContextDict: TypeAlias = Dict[str, Any]
ResultDict: TypeAlias = Dict[str, Any]
StructureMap: TypeAlias = Dict[str, List[str]]

class StructureBot(BaseAgent):
    """Keeps the codebase organized"""

    def __init__(
        self,
        graph: Optional[Any] = None,
        llm_client: Optional[Any] = None
    ) -> None:
        """Initialize StructureBot with graph and optional LLM client.

        Args:
            graph: Optional knowledge graph instance
            llm_client: Optional LLM client for generation
        """
        super().__init__("StructureBot", graph, llm_client)
        self.vibe: str = "organized"
        self.project_root: str = "/Users/mdawson/Dawson/DawsOSB/dawsos"

    def get_prompt(self, context: ContextDict) -> str:
        """Generate prompt for file organization decisions.

        Args:
            context: Dictionary containing functionality details

        Returns:
            Formatted prompt string
        """
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

    def find_home(self, functionality: str) -> ResultDict:
        """Find where new functionality should live.

        Args:
            functionality: Description of new functionality

        Returns:
            Dictionary with folder, filename, reason, and full_path
        """
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

    def suggest_refactor(self, file_path: str, line_count: int) -> ResultDict:
        """Suggest how to refactor a large file.

        Args:
            file_path: Path to file being analyzed
            line_count: Number of lines in the file

        Returns:
            Dictionary with refactoring suggestions
        """
        context = {
            "file_path": file_path,
            "line_count": line_count,
            "question": "Should we split this file?"
        }
        return self.think(context)

    def scan_structure(self) -> ResultDict:
        """Scan project structure and suggest improvements.

        Returns:
            Dictionary with structure analysis and suggestions
        """
        structure = self._get_project_structure()

        context = {
            "structure": structure,
            "question": "Any organization improvements needed?"
        }
        return self.think(context)

    def _get_project_structure(self) -> StructureMap:
        """Get current project structure.

        Returns:
            Dictionary mapping folder paths to lists of files
        """
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

    def __init__(self, llm_client: Optional[Any] = None) -> None:
        """Initialize FileCreator with optional LLM client.

        Args:
            llm_client: Optional LLM client for generation
        """
        super().__init__("FileCreator", None, llm_client)
        self.vibe: str = "creative"

    def get_prompt(self, context: ContextDict) -> str:
        """Generate prompt for file creation.

        Args:
            context: Dictionary with file_type, purpose, filename

        Returns:
            Formatted prompt string
        """
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

    def __init__(self, llm_client: Optional[Any] = None) -> None:
        """Initialize FolderOrganizer with optional LLM client.

        Args:
            llm_client: Optional LLM client for generation
        """
        super().__init__("FolderOrganizer", None, llm_client)
        self.vibe: str = "systematic"

    def get_prompt(self, context: ContextDict) -> str:
        """Generate prompt for folder organization.

        Args:
            context: Dictionary with folders and new_items

        Returns:
            Formatted prompt string
        """
        return f"""
        Suggest folder organization.

        Current folders: {context.get('folders', [])}
        New items to organize: {context.get('new_items', [])}

        Where should each item go? Be consistent with existing patterns.
        """