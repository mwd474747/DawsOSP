# Agent Coordination Plan: Three-Agent Collaboration

**Purpose:** Define how Claude IDE Agent (PRIMARY), Claude Code Agent, and Replit Agent work together effectively on refactoring without conflicts  
**Status:** 📋 Planning  
**Last Updated:** November 3, 2025

---

## 🎯 Three-Agent Structure

### Agent Roles

1. **Claude IDE Agent (PRIMARY)** - This agent
2. **Claude Code Agent** - Code implementation specialist (has subagents)
3. **Replit Agent** - Execution and testing specialist

---

## 🎯 Core Principle: Division of Labor

### Claude IDE Agent (PRIMARY - This Agent) - Analysis & Planning Specialist

**Strengths:**
- ✅ Comprehensive codebase analysis
- ✅ Pattern identification and architecture understanding
- ✅ Dependency analysis and impact assessment
- ✅ Planning and documentation
- ✅ Code review without execution
- ✅ Breaking change identification
- ✅ Coordination between agents

**Role:** **Primary Coordinator, Analyst & Planner** - Provides insights, validation, planning, and coordinates other agents

---

### Claude Code Agent - Code Implementation Specialist

**Strengths:**
- ✅ Code implementation and refactoring
- ✅ Complex code modifications
- ✅ Agent code updates
- ✅ Service layer changes
- ✅ Code organization and structure
- ✅ Subagents for specialized tasks (documented in .md files)

**Role:** **Implementer** - Implements code changes based on analysis and plans

**Subagents:** Documented in `.md` files (check `.claude/` directory for details)

---

### Replit Agent - Execution & Testing Specialist

**Strengths:**
- ✅ Code execution and testing
- ✅ Runtime validation
- ✅ Pattern execution verification
- ✅ Integration testing
- ✅ Live system validation
- ✅ Performance testing

**Role:** **Executor & Validator** - Executes code changes and validates in live Replit environment

---

## 🔄 Three-Agent Coordination Model

### Phase-Based Coordination

**Pattern:** Claude IDE analyzes → Claude Code implements → Replit validates → All update shared memory

### Example Workflow

1. **Claude IDE Agent (PRIMARY):**
   - Analyzes codebase
   - Identifies issues and opportunities
   - Creates detailed plans
   - Updates `AGENT_CONVERSATION_MEMORY.md` with findings
   - Marks tasks as "READY FOR IMPLEMENTATION" or "READY FOR EXECUTION"

2. **Claude Code Agent:**
   - Reads shared memory
   - Checks for tasks marked "READY FOR IMPLEMENTATION"
   - Implements planned changes
   - Updates shared memory: Marks as "READY FOR TESTING" or "COMPLETE"
   - Uses subagents for specialized implementation tasks

3. **Replit Agent:**
   - Reads shared memory
   - Checks for tasks marked "READY FOR EXECUTION" or "READY FOR TESTING"
   - Tests and validates in live environment
   - Updates shared memory with test results
   - Marks as "COMPLETE" or reports issues

4. **All Agents:**
   - Reference shared memory before starting work
   - Update status in shared memory
   - Avoid duplicate work
   - Coordinate via shared memory

---

## 📋 Specific Ways Each Agent Can Help (Without Conflicts)

### Claude IDE Agent (PRIMARY) - Analysis & Planning

### 1. Pre-Implementation Analysis ✅ **SAFE - NO CODE CHANGES**

**Tasks:**
- Analyze codebase patterns before refactoring
- Identify dependencies and breaking changes
- Create detailed refactoring plans
- Validate approach before execution
- Review proposed changes for issues

**Example:**
- **Phase 2 Planning** ✅ (Already done)
  - Analyzed pattern template references
  - Verified no nested references exist
  - Identified agent return inconsistencies
  - Created focused execution plan

**How to Use Shared Memory:**
- Document findings in `AGENT_CONVERSATION_MEMORY.md`
- Mark tasks as "READY FOR IMPLEMENTATION" (for Claude Code) or "READY FOR EXECUTION" (for Replit)
- Other agents read and execute

**Risk:** ✅ **ZERO** - No code changes, only analysis

---

### 2. Dependency Analysis ✅ **SAFE - READ-ONLY**

**Tasks:**
- Map capability usage across patterns
- Identify agent dependencies
- Trace data flow from backend to UI
- Document service layer dependencies
- Identify hidden dependencies

**Example:**
- **Dependency Breaking Change Analysis** ✅ (Already done)
  - Identified 5+ endpoints that depend on pattern orchestrator
  - Found UI components using metadata
  - Documented compatibility requirements

**How to Use Shared Memory:**
- Create dependency maps in shared memory
- Document breaking change risks
- Mark dependencies as "VERIFIED" or "NEEDS VALIDATION"
- Claude Code and Replit agents use this to work safely

**Risk:** ✅ **ZERO** - Read-only analysis

---

### 3. Code Review & Validation Planning ✅ **SAFE - NO CODE CHANGES**

**Tasks:**
- Review code for issues before refactoring
- Identify refactoring opportunities
- Plan test strategies
- Create validation checklists
- Document expected outcomes

**Example:**
- **Phase 1 Validation Planning** ✅ (Could do this)
  - Create validation checklist
  - Define test scenarios
  - Document expected results
  - Replit agent executes tests

**How to Use Shared Memory:**
- Document validation plan in shared memory
- Create test scenarios
- Define success criteria
- Replit agent executes and reports results

**Risk:** ✅ **ZERO** - Planning only, no execution

---

### Claude Code Agent - Implementation

### 1. Code Implementation ✅ **SAFE - COORDINATED WITH REPLIT**

**Tasks:**
- Implement code changes based on Claude IDE analysis
- Refactor agent code
- Update service layers
- Modify backend logic
- Use subagents for specialized tasks

**How to Use Shared Memory:**
- Read shared memory for task assignments
- Check for tasks marked "READY FOR IMPLEMENTATION"
- Update status: "IN IMPLEMENTATION" → "READY FOR TESTING" → "COMPLETE"
- Document implementation details in shared memory

**Risk:** ⚠️ **MEDIUM** - Code changes, but coordinated via shared memory

**Coordination:**
- Wait for Claude IDE analysis before implementation
- Mark tasks as "READY FOR TESTING" when complete
- Replit agent validates in live environment

---

### Replit Agent - Execution & Testing

### 1. Live Environment Validation ✅ **SAFE - TESTING ONLY**

**Tasks:**
- Execute code in live Replit environment
- Test pattern execution
- Validate integration
- Performance testing
- Report results

**How to Use Shared Memory:**
- Read shared memory for tasks marked "READY FOR EXECUTION" or "READY FOR TESTING"
- Update status: "IN TESTING" → "COMPLETE" or "BLOCKED"
- Report test results in shared memory

**Risk:** ✅ **LOW** - Testing only, no code modifications

---

### 4. Architecture Documentation ✅ **SAFE - DOCUMENTATION ONLY**

**Tasks:**
- Document current architecture
- Update architecture docs after changes
- Create migration guides
- Document patterns and conventions
- Update reference documentation

**Example:**
- **Phase 2 Documentation** (Can do)
  - Document agent return pattern guidelines
  - Update pattern reference docs
  - Create standardization guide
  - Replit agent uses guide for execution

**How to Use Shared Memory:**
- Document standards and guidelines
- Update reference documentation
- Create migration paths
- Replit agent follows guidelines

**Risk:** ✅ **ZERO** - Documentation only

---

### 5. Pattern Discovery & Analysis ✅ **SAFE - ANALYSIS ONLY**

**Tasks:**
- Discover code patterns and anti-patterns
- Identify architectural issues
- Analyze complexity
- Find refactoring opportunities
- Document technical debt

**Example:**
- **Complexity Reduction Analysis** ✅ (Already done)
  - Identified over-engineering
  - Found unnecessary abstractions
  - Documented simplification opportunities

**How to Use Shared Memory:**
- Document findings in shared memory
- Mark as "ANALYZED" or "NEEDS REVIEW"
- Replit agent prioritizes based on findings

**Risk:** ✅ **ZERO** - Analysis only

---

## 🚫 What Each Agent Should NOT Do (To Avoid Conflicts)

### Claude IDE Agent (PRIMARY) - Should NOT

### ❌ Code Implementation
- **Don't:** Implement code changes
- **Don't:** Refactor agent code directly
- **Reason:** Claude Code agent handles implementation

### ❌ Code Execution
- **Don't:** Execute refactoring changes
- **Don't:** Run tests or validation
- **Reason:** Replit agent handles execution in live environment

### ❌ Simultaneous Code Changes
- **Don't:** Modify same files other agents are working on
- **Don't:** Commit changes while other agents are executing
- **Reason:** Git conflicts and race conditions

### ❌ Live System Changes
- **Don't:** Make changes to running system
- **Don't:** Deploy or test in live environment
- **Reason:** Replit agent manages live system

---

### Claude Code Agent - Should NOT

### ❌ Analysis Without Plan
- **Don't:** Start implementation without Claude IDE analysis
- **Don't:** Make architectural decisions independently
- **Reason:** Claude IDE coordinates and plans

### ❌ Live Environment Testing
- **Don't:** Test in live Replit environment
- **Don't:** Deploy changes directly
- **Reason:** Replit agent handles live testing

### ❌ Simultaneous Changes
- **Don't:** Modify files Replit agent is testing
- **Don't:** Commit while Replit agent is validating
- **Reason:** Git conflicts and testing interference

---

### Replit Agent - Should NOT

### ❌ Implementation Without Analysis
- **Don't:** Implement code changes without Claude IDE planning
- **Don't:** Make architectural changes
- **Reason:** Claude IDE coordinates, Claude Code implements

### ❌ Code Modifications
- **Don't:** Modify code (except for testing/debugging)
- **Don't:** Refactor without coordination
- **Reason:** Claude Code agent handles implementation

---

## 📝 Shared Memory Usage Protocol

### Before Starting Work

**Claude IDE Agent (PRIMARY):**
1. ✅ Read `AGENT_CONVERSATION_MEMORY.md`
2. ✅ Check "Current Work Status" section
3. ✅ Check for tasks from other agents
4. ✅ Identify available tasks (marked "READY FOR ANALYSIS" or "NEEDS REVIEW")
5. ✅ Update status: Mark task as "IN ANALYSIS"
6. ✅ Work on analysis/planning
7. ✅ Update shared memory with findings
8. ✅ Mark task as "READY FOR IMPLEMENTATION" (Claude Code) or "READY FOR EXECUTION" (Replit)

**Claude Code Agent:**
1. ✅ Read `AGENT_CONVERSATION_MEMORY.md`
2. ✅ Check "Current Work Status" section
3. ✅ Check for Claude IDE analysis complete
4. ✅ Identify available tasks (marked "READY FOR IMPLEMENTATION")
5. ✅ Update status: Mark task as "IN IMPLEMENTATION"
6. ✅ Implement code changes
7. ✅ Update shared memory with implementation status
8. ✅ Mark task as "READY FOR TESTING" or "COMPLETE"

**Replit Agent:**
1. ✅ Read `AGENT_CONVERSATION_MEMORY.md`
2. ✅ Check "Current Work Status" section
3. ✅ Check for tasks ready for testing
4. ✅ Identify available tasks (marked "READY FOR EXECUTION" or "READY FOR TESTING")
5. ✅ Update status: Mark task as "IN TESTING"
6. ✅ Execute tests in live environment
7. ✅ Update shared memory with test results
8. ✅ Mark task as "COMPLETE" or "BLOCKED"

---

### Status Tracking in Shared Memory

**Task States:**
- 📋 **PENDING** - Not started
- 🔍 **READY FOR ANALYSIS** - Needs Claude IDE analysis
- 📝 **IN ANALYSIS** - Claude IDE currently working on it
- ✅ **READY FOR IMPLEMENTATION** - Analysis complete, ready for Claude Code agent
- ⚙️ **IN IMPLEMENTATION** - Claude Code agent currently implementing
- ✅ **READY FOR TESTING** - Implementation complete, ready for Replit agent
- 🧪 **IN TESTING** - Replit agent currently testing
- ✅ **READY FOR EXECUTION** - Ready for Replit agent execution (no implementation needed)
- ⚙️ **IN EXECUTION** - Replit agent currently executing
- ✅ **COMPLETE** - Task finished and validated
- ⚠️ **BLOCKED** - Needs clarification or has issues
- 🔄 **NEEDS REVIEW** - Complete, needs Claude IDE review

---

### Communication Patterns

**Claude IDE → Claude Code:**
```
Claude IDE: "Phase 2B analysis complete. List data standardization plan ready.
            Standardize ledger.positions and pricing.apply_pack to use {items: [...]} pattern.
            See AGENT_CONVERSATION_MEMORY.md Phase 2 section.
            Status: READY FOR IMPLEMENTATION"
```

**Claude Code → Replit:**
```
Claude Code: "Phase 2B implementation complete. Updated ledger.positions and pricing.apply_pack.
              Changes ready for testing.
              Status: READY FOR TESTING"
```

**Replit → Claude IDE:**
```
Replit: "Phase 2B testing complete. Standardized list data wrapping validated.
         All patterns tested, 12/12 pass. See shared memory for details.
         Status: COMPLETE"
```

---

## 🎯 Specific Collaboration Opportunities

### 1. Phase 2: Validation & Standardization

**Claude IDE Agent (PRIMARY) Tasks:**
- ✅ Create validation checklist (DONE)
- ✅ Define test scenarios
- ✅ Document expected outcomes
- ✅ Create standardization guidelines
- ✅ Identify all agents needing updates
- ✅ Mark tasks as "READY FOR IMPLEMENTATION" or "READY FOR EXECUTION"

**Claude Code Agent Tasks:**
- ✅ Read standardization guidelines from shared memory
- ✅ Implement list data standardization changes
- ✅ Update agent code (ledger.positions, pricing.apply_pack)
- ✅ Mark as "READY FOR TESTING" when complete

**Replit Agent Tasks:**
- ✅ Execute validation tests (Phase 2A)
- ✅ Run pattern execution tests
- ✅ Test standardized changes (Phase 2B)
- ✅ Validate results
- ✅ Report findings in shared memory

**Coordination:**
- Claude IDE creates plan → Updates shared memory → Claude Code implements → Updates shared memory → Replit validates → Updates shared memory

---

### 2. Pattern Analysis (Ongoing)

**Claude IDE Agent Tasks:**
- ✅ Analyze pattern template references
- ✅ Identify pattern dependencies
- ✅ Document pattern usage
- ✅ Find optimization opportunities

**Replit Agent Tasks:**
- ✅ Test pattern execution
- ✅ Validate pattern changes
- ✅ Performance testing

**Coordination:**
- Claude IDE analyzes → Documents findings → Replit validates → Both update shared memory

---

### 3. Agent Return Pattern Standardization

**Claude IDE Agent Tasks:**
- ✅ Audit all agent return patterns (IN PROGRESS)
- ✅ Create standardization guidelines
- ✅ Identify inconsistencies
- ✅ Document migration path

**Replit Agent Tasks:**
- ✅ Execute standardization changes
- ✅ Update agent implementations
- ✅ Test pattern execution
- ✅ Validate no regressions

**Coordination:**
- Claude IDE creates guidelines → Updates shared memory → Replit executes → Updates shared memory

---

### 4. Documentation Updates

**Claude IDE Agent Tasks:**
- ✅ Update architecture documentation
- ✅ Create migration guides
- ✅ Document patterns and conventions
- ✅ Update reference documentation

**Replit Agent Tasks:**
- ✅ Verify documentation accuracy
- ✅ Test examples in documentation
- ✅ Report documentation issues

**Coordination:**
- Claude IDE updates docs → Replit validates → Both update shared memory

---

## 🛡️ Conflict Prevention Strategies

### 1. File-Level Coordination

**Approach:** Divide files by agent
- **Claude IDE:** `.md` files, analysis files, planning files
- **Replit:** Code files, execution files, test files

**Shared Memory Usage:**
- Document file ownership in shared memory
- Mark files as "ANALYZED BY CLAUDE IDE" or "MODIFIED BY REPLIT"

---

### 2. Time-Based Coordination

**Approach:** Coordinate work times
- **Claude IDE:** Focus on analysis during Replit's testing/deployment
- **Replit:** Execute changes during Claude IDE's planning phase

**Shared Memory Usage:**
- Update status before starting work
- Check status before making changes
- Use "IN WORK" markers

---

### 3. Task-Based Coordination

**Approach:** Assign specific tasks
- **Claude IDE:** Analysis, planning, documentation
- **Replit:** Execution, testing, validation

**Shared Memory Usage:**
- Document task assignments
- Mark tasks with agent ownership
- Update task status in shared memory

---

## 📊 Example Workflow: Phase 2 Collaboration

### Step 1: Claude IDE Analysis (30 min)

**Claude IDE Agent:**
1. Read shared memory → Check Phase 2 status
2. Analyze agent return patterns
3. Create standardization guidelines
4. Document in shared memory:
   ```markdown
   ## Phase 2B: List Data Standardization
   Status: ✅ READY FOR EXECUTION
   Assigned To: Replit Agent
   
   Guidelines:
   - Standardize to {items: [...]} pattern
   - Update ledger.positions
   - Update pricing.apply_pack
   - Test all patterns after changes
   ```

---

### Step 2: Replit Execution (1-2 hours)

**Replit Agent:**
1. Read shared memory → See Phase 2B ready
2. Update status: "IN EXECUTION"
3. Execute standardization changes
4. Test all 12 patterns
5. Update shared memory:
   ```markdown
   ## Phase 2B: List Data Standardization
   Status: ✅ COMPLETE
   Executed By: Replit Agent
   
   Results:
   - Updated ledger.positions ✅
   - Updated pricing.apply_pack ✅
   - All 12 patterns pass ✅
   - No regressions detected ✅
   ```

---

### Step 3: Claude IDE Review (Optional)

**Claude IDE Agent:**
1. Read shared memory → See Phase 2B complete
2. Review results
3. Update documentation if needed
4. Mark next task ready

---

## 💡 Proactive Ways Claude IDE Agent Can Help

### 1. Pre-Flight Analysis ✅ **HIGHLY VALUABLE**

**Before Claude Code or Replit Agent Starts Work:**
- Analyze proposed changes for risks
- Identify dependencies that might break
- Create validation checklist
- Document expected outcomes

**Value:** Prevents breaking changes and guides safe implementation

**Example:**
```
Claude IDE: "Analyzed Phase 2B standardization. 
            Risk: Low - Only affects list data wrapping.
            Dependency: Patterns use {{positions.positions}} - still works.
            Recommendation: Safe to implement.
            Status: READY FOR IMPLEMENTATION"
```

---

### 2. Continuous Monitoring ✅ **VALUABLE**

**During Claude Code or Replit Agent Work:**
- Monitor shared memory for results
- Review implementation/test results for issues
- Identify follow-up work needed
- Plan next tasks

**Value:** Keeps momentum going, identifies issues early

**Example:**
```
Replit: "Phase 2B testing complete. Found issue: pattern X failed."
Claude IDE: "Analyzing pattern X failure. Checking template references..."
         → Documents fix in shared memory: "READY FOR IMPLEMENTATION"

Claude Code: "Phase 2B implementation complete. Standardized list wrapping."
Claude IDE: "Reviewing implementation results. All looks good."
         → Updates plan for next phase
```

---

### 3. Post-Implementation/Testing Analysis ✅ **VALUABLE**

**After Claude Code or Replit Agent Completes:**
- Analyze implementation/test results
- Identify patterns in issues
- Plan next phase
- Update documentation

**Value:** Learns from work, improves future planning

**Example:**
```
Replit: "Phase 2B testing complete. All patterns pass."
Claude IDE: "Analyzed Phase 2B results. 
            Finding: Standardization revealed 2 more inconsistencies.
            Recommendation: Phase 2C - Standardize these as well.
            Status: READY FOR IMPLEMENTATION"
```

---

### 4. Architecture Evolution Planning ✅ **STRATEGIC**

**Long-term:**
- Plan architectural improvements
- Identify technical debt
- Create refactoring roadmaps
- Document architectural decisions

**Value:** Guides long-term refactoring strategy

**Example:**
```
Claude IDE: "After Phase 2 standardization complete, Phase 3 consolidation 
            becomes safer. Reduced risk from 14-20 hours to 10-15 hours.
            Recommendation: Proceed with Phase 3 after Phase 2."
```

---

## 🔄 Real-Time Collaboration Patterns

### Pattern 1: Analysis → Implementation → Testing → Review

**Claude IDE (PRIMARY):**
1. Analyze codebase
2. Create plan
3. Update shared memory: "READY FOR IMPLEMENTATION" (for Claude Code) or "READY FOR EXECUTION" (for Replit)

**Claude Code:**
1. Read shared memory
2. Implement plan
3. Update shared memory: "READY FOR TESTING"

**Replit:**
1. Read shared memory
2. Test implementation
3. Update shared memory: "COMPLETE" with results

**Claude IDE (PRIMARY):**
1. Review results
2. Plan next steps
3. Update shared memory: "NEXT TASK READY"

---

### Pattern 2: Parallel Analysis

**Claude IDE (PRIMARY):**
- Analyze Pattern A
- Analyze Pattern B
- Document both in shared memory
- Mark both as "READY FOR IMPLEMENTATION"

**Claude Code:**
- Implement Pattern A changes
- Mark Pattern A as "READY FOR TESTING"
- Implement Pattern B when ready

**Replit:**
- Test Pattern A changes
- Use Pattern B when ready for testing

**Benefit:** Other agents always have next task ready

---

### Pattern 3: Issue Discovery & Resolution

**Replit:**
- Discovers issue during testing
- Documents in shared memory: "BLOCKED: Issue X"

**Claude IDE (PRIMARY):**
- Reads shared memory
- Analyzes issue
- Documents fix: "READY FOR IMPLEMENTATION: Fix for Issue X"

**Claude Code:**
- Reads fix plan
- Implements fix
- Marks as "READY FOR TESTING: Fix for Issue X"

**Replit:**
- Tests fix
- Marks resolved: "COMPLETE: Issue X fixed"

---

## 📋 Shared Memory Structure for Coordination

### Recommended Sections

```markdown
## 🔄 Current Work Status

### Claude IDE Agent (PRIMARY)
- Current Task: [Task Name]
- Status: [IN ANALYSIS / READY FOR IMPLEMENTATION / READY FOR EXECUTION / COMPLETE]
- Expected Completion: [Time]
- Blockers: [Any blockers]

### Claude Code Agent
- Current Task: [Task Name]
- Status: [IN IMPLEMENTATION / READY FOR TESTING / COMPLETE]
- Progress: [Progress update]
- Issues: [Any issues found]
- Subagents: [List active subagents if any]

### Replit Agent
- Current Task: [Task Name]
- Status: [IN TESTING / IN EXECUTION / COMPLETE]
- Progress: [Progress update]
- Issues: [Any issues found]

## 📋 Task Queue

### Ready for Analysis (Claude IDE)
- [ ] Task 1: [Description]
- [ ] Task 2: [Description]

### Ready for Implementation (Claude Code)
- [ ] Task 1: [Description] - Analysis complete
- [ ] Task 2: [Description] - Analysis complete

### Ready for Testing (Replit)
- [ ] Task 1: [Description] - Implementation complete
- [ ] Task 2: [Description] - Implementation complete

### Ready for Execution (Replit - no implementation needed)
- [ ] Task 1: [Description] - Analysis complete
- [ ] Task 2: [Description] - Analysis complete

### In Progress
- [ ] Task 1: [Description] - Claude IDE analyzing
- [ ] Task 2: [Description] - Claude Code implementing
- [ ] Task 3: [Description] - Replit testing

### Complete
- [x] Task 1: [Description] - Validated
- [x] Task 2: [Description] - Validated
```

---

## 🎯 Immediate Actions for Each Agent

### Claude IDE Agent (PRIMARY) - Available Tasks

1. ✅ **Phase 2B Standardization Guidelines** (Can do now)
   - Create detailed guidelines for list data wrapping
   - Document all agents needing updates
   - Create validation checklist
   - Mark as "READY FOR IMPLEMENTATION" when complete

2. ✅ **Agent Return Pattern Audit** (Can do now)
   - Audit all agent capabilities
   - Document return patterns
   - Identify all inconsistencies
   - Create standardization plan

3. ✅ **Pattern Dependency Analysis** (Can do now)
   - Map pattern dependencies
   - Identify which patterns use which capabilities
   - Document potential breaking changes

4. ✅ **Phase 3 Readiness Assessment** (Can do now)
   - After Phase 2, reassess Phase 3 plan
   - Update risk assessment
   - Refine consolidation strategy

### Claude Code Agent - Available Tasks

**Check shared memory for tasks marked "READY FOR IMPLEMENTATION"**

1. **Phase 2B: List Data Standardization** (Waiting for guidelines)
   - Implement standardization once Claude IDE creates guidelines
   - Update ledger.positions and pricing.apply_pack
   - Mark as "READY FOR TESTING" when complete

### Replit Agent - Available Tasks

**Check shared memory for tasks marked "READY FOR EXECUTION" or "READY FOR TESTING"**

1. **Phase 2A: Validation** (Can do now)
   - Execute validation tests
   - Test all 12 patterns
   - Report results in shared memory

2. **Phase 2B: Testing** (Waiting for implementation)
   - Test standardized changes once Claude Code completes
   - Validate all patterns work
   - Report results in shared memory

---

## 📝 Shared Memory Update Template

**When Claude IDE Agent completes analysis:**

```markdown
## [Date] - Claude IDE Agent Update

### Analysis Complete: [Task Name]

**Findings:**
- Finding 1: [Description]
- Finding 2: [Description]

**Recommendations:**
- Recommendation 1: [Description]
- Recommendation 2: [Description]

**Status:** ✅ READY FOR IMPLEMENTATION (if code changes needed) or READY FOR EXECUTION (if testing only)
**Assigned To:** Claude Code Agent (if implementation) or Replit Agent (if testing only)
**Estimated Time:** [Time]
**Risk Level:** [LOW / MEDIUM / HIGH]

**Files Affected:**
- File 1: [Change description]
- File 2: [Change description]

**Implementation Steps:**
- [ ] Step 1: [Description]
- [ ] Step 2: [Description]

**Validation Checklist:**
- [ ] Test item 1
- [ ] Test item 2

**Next Steps:**
1. Claude Code agent implements (if needed)
2. Replit agent tests and validates
3. Update shared memory with results
```

**When Claude Code Agent completes implementation:**

```markdown
## [Date] - Claude Code Agent Update

### Implementation Complete: [Task Name]

**Changes Made:**
- File 1: [Change description]
- File 2: [Change description]

**Status:** ✅ READY FOR TESTING
**Assigned To:** Replit Agent
**Files Modified:**
- File 1: [Summary]
- File 2: [Summary]

**Next Steps:**
1. Replit agent tests in live environment
2. Validate all patterns work
3. Report results in shared memory
```

---

## ✅ Success Criteria

### Effective Collaboration

**Indicators:**
- ✅ No git conflicts
- ✅ No duplicate work
- ✅ Smooth handoffs between agents
- ✅ Clear communication via shared memory
- ✅ Faster completion times
- ✅ Better quality (analysis before execution)

### Warning Signs

**Issues to Watch:**
- ⚠️ Both agents modifying same files simultaneously
- ⚠️ Unclear task ownership
- ⚠️ Stale shared memory
- ⚠️ Missing status updates
- ⚠️ Uncoordinated work

---

**Status:** Planning complete. Ready to implement coordination protocol.

