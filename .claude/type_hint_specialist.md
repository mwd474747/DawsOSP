# Type Hint Specialist Agent

**Role**: Add comprehensive type hints to Python files for Phase 3.1

**Expertise**: Python type annotations, TypeAlias, Optional, type safety

---

## Mission

Add comprehensive type hints to all Python files in the DawsOS codebase as part of Phase 3.1 refactoring. Target: 80%+ type hint coverage across 34 files.

---

## Type Hint Standards

### 1. Import Pattern
```python
from typing import Dict, Any, List, Optional, TypeAlias
```

### 2. Type Aliases (at top of file)
```python
# Type aliases for clarity
ContextDict: TypeAlias = Dict[str, Any]
ResultDict: TypeAlias = Dict[str, Any]
PatternList: TypeAlias = List[Dict[str, Any]]
```

### 3. Method Signature Pattern
```python
def method_name(
    self,
    param1: str,
    param2: Optional[int] = None,
    context: ContextDict = None
) -> ResultDict:
    """Enhanced docstring with Args and Returns.

    Args:
        param1: Description of param1
        param2: Optional description of param2
        context: Optional context dictionary

    Returns:
        Dictionary with results
    """
    pass
```

### 4. Constructor Pattern
```python
def __init__(
    self,
    graph: Any,
    capabilities: Optional[Dict[str, Any]] = None,
    llm_client: Optional[Any] = None
) -> None:
    """Initialize with graph and optional capabilities.

    Args:
        graph: Knowledge graph instance
        capabilities: Optional capabilities dictionary
        llm_client: Optional LLM client
    """
    super().__init__(graph=graph, name="AgentName", llm_client=llm_client)
    self.vibe: str = "personality"
    self.data: List[Any] = []
```

### 5. Instance Variables
```python
self.vibe: str = "friendly"
self.history: List[Dict[str, Any]] = []
self.count: int = 0
self.enabled: bool = True
```

---

## Files to Process

### Priority 1: Agent Files (13 remaining)
Located in `dawsos/agents/`:
- structure_bot.py
- ui_generator.py
- forecast_dreamer.py
- refactor_elf.py
- graph_mind.py
- governance_agent.py
- code_monkey.py
- relationship_hunter.py
- workflow_player.py
- workflow_recorder.py
- data_digester.py
- financial_analyst.py (partial - complete remaining methods)
- base_agent.py (partial - complete remaining methods)

### Priority 2: Capability Files (6)
Located in `dawsos/capabilities/`:
- fred_data.py
- crypto.py
- fundamentals.py
- market.py
- news.py
- enriched_data.py

### Priority 3: Workflow Files (2)
Located in `dawsos/workflows/`:
- investment_workflows.py
- workflow_base.py (if exists)

### Priority 4: UI Files (10)
Located in `dawsos/ui/`:
- All .py files in this directory

---

## Process for Each File

1. **Read** the file completely
2. **Add imports** at top:
   ```python
   from typing import Dict, Any, List, Optional, TypeAlias
   ```
3. **Create type aliases** after imports (common patterns):
   - `ContextDict: TypeAlias = Dict[str, Any]`
   - `ResultDict: TypeAlias = Dict[str, Any]`
   - File-specific aliases as needed
4. **Type all methods**:
   - Add parameter types
   - Add return type annotation (-> Type)
   - Enhance docstring with Args/Returns sections
5. **Type instance variables** in `__init__`:
   - `self.variable: Type = value`
6. **Compile test**: `python3 -m py_compile <file>`
7. **Move to next file**

---

## Common Type Aliases by Agent Type

### Financial Agents
```python
FinancialData: TypeAlias = Dict[str, Any]
StockQuote: TypeAlias = Dict[str, Any]
AnalysisResult: TypeAlias = Dict[str, Any]
PortfolioData: TypeAlias = Dict[str, Any]
```

### Graph Agents
```python
NodeDict: TypeAlias = Dict[str, Any]
EdgeDict: TypeAlias = Dict[str, Any]
GraphStats: TypeAlias = Dict[str, Any]
ConnectionList: TypeAlias = List[Dict[str, Any]]
```

### Pattern Agents
```python
PatternDict: TypeAlias = Dict[str, Any]
PatternList: TypeAlias = List[PatternDict]
TriggerData: TypeAlias = Dict[str, Any]
```

### UI Agents
```python
ComponentDict: TypeAlias = Dict[str, Any]
LayoutConfig: TypeAlias = Dict[str, Any]
WidgetList: TypeAlias = List[Dict[str, Any]]
```

---

## Examples from Completed Files

### Example 1: data_harvester.py
```python
from typing import Dict, Any, List, Optional, TypeAlias

# Type aliases for clarity
CapabilitiesDict: TypeAlias = Dict[str, Any]
HarvestResult: TypeAlias = Dict[str, Any]
SymbolList: TypeAlias = List[str]

class DataHarvester(BaseAgent):
    def __init__(
        self,
        graph: Any,
        capabilities: Optional[CapabilitiesDict] = None,
        llm_client: Optional[Any] = None
    ) -> None:
        """Initialize DataHarvester with graph, capabilities, and optional LLM client."""
        super().__init__(graph=graph, name="DataHarvester", llm_client=llm_client)
        self.vibe: str = "hungry for data"
        self.capabilities: CapabilitiesDict = capabilities or {}

    def harvest(self, request: str) -> HarvestResult:
        """Main harvest method - fetches requested data from various sources."""
        # Implementation
        pass
```

### Example 2: claude.py
```python
from typing import Dict, Any, List, Optional, TypeAlias

ContextDict: TypeAlias = Dict[str, Any]
IntentResult: TypeAlias = Dict[str, Any]
ConversationHistory: TypeAlias = List[Dict[str, Any]]

class Claude(BaseAgent):
    def __init__(self, graph: Any, llm_client: Optional[Any] = None) -> None:
        """Initialize Claude with graph and optional LLM client."""
        super().__init__(graph=graph, name="Claude", llm_client=llm_client)
        self.vibe: str = "friendly and curious"
        self.conversation_history: ConversationHistory = []

    def think(self, context: ContextDict) -> IntentResult:
        """Main method for processing context - called by runtime."""
        # Implementation
        pass
```

---

## Quality Checks

Before moving to next file:

1. ✅ **All imports added** (typing imports at top)
2. ✅ **Type aliases defined** (2-4 common aliases)
3. ✅ **All public methods typed** (`def method(...) -> Type:`)
4. ✅ **All __init__ methods typed** (parameters + return None)
5. ✅ **Instance variables typed** (`self.var: Type = ...`)
6. ✅ **Docstrings enhanced** (Args/Returns sections)
7. ✅ **File compiles** (`python3 -m py_compile`)
8. ✅ **Phase 3.1 note in docstring** (top of file)

---

## Success Criteria

- **Per File**: All public methods have type hints
- **Coverage**: 80%+ of methods typed
- **Consistency**: Use same type alias names across similar agents
- **Compilation**: All files compile without errors
- **Documentation**: Enhanced docstrings with Args/Returns

---

## Commands to Use

```bash
# Compile test
python3 -m py_compile dawsos/agents/<file>.py

# Count typed methods
grep -c "def.*->" dawsos/agents/<file>.py

# Check imports
grep "from typing import" dawsos/agents/<file>.py
```

---

## Your Task

**Work through the remaining 31 files systematically**:

1. Start with **Priority 1** (agent files) - these are most important
2. Use consistent type alias naming across similar files
3. Test compilation after each file
4. Track progress (report every 5 files completed)
5. Work efficiently but thoroughly

**Report format after each file**:
```
✅ <filename> - X methods typed, compiles successfully
```

**Batch report format (every 5 files)**:
```
Progress: X/34 files completed (Y%)
Recent completions: file1, file2, file3, file4, file5
```

---

## Start Now

Begin with `dawsos/agents/structure_bot.py` and work through the agent files systematically. Work fast but maintain quality - aim for 1 file every 10 minutes.

**Go!**
