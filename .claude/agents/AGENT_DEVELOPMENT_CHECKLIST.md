# DawsOS Agent Development Checklist

**Date**: October 27, 2025  
**Purpose**: Standardized process for agent development and maintenance  
**Status**: ✅ Complete and Ready for Use

---

## 🎯 **OVERVIEW**

This checklist ensures consistent, high-quality agent development following DawsOS architectural patterns and best practices.

---

## 📋 **PRE-DEVELOPMENT CHECKLIST**

### **Prerequisites Verification**
- [ ] **Read PRODUCT_SPEC.md** - Understand acceptance criteria and requirements
- [ ] **Review ORCHESTRATOR.md** - Understand system architecture and patterns
- [ ] **Check IMPLEMENTATION_STATUS_MATRIX.md** - Verify current implementation state
- [ ] **Review existing agent specifications** - Understand patterns and conventions

### **Infrastructure Verification**
- [ ] **Database migrations applied** - Check required schema exists
- [ ] **Services available** - Verify service dependencies exist
- [ ] **API keys configured** - Check provider API keys if needed
- [ ] **Seed data loaded** - Verify test data available

### **File Existence Verification**
```bash
# Check these files exist before starting
ls backend/app/services/<service_name>.py
ls backend/app/agents/<agent_name>.py
ls backend/patterns/<pattern_name>.json
ls backend/db/schema/<schema_name>.sql
```

---

## 🔧 **SERVICE IMPLEMENTATION CHECKLIST**

### **Service Creation/Update**
- [ ] **Create service class** with async methods
- [ ] **Implement business logic** (NO shortcuts or stubs)
- [ ] **Add error handling** and graceful degradation
- [ ] **Add logging** with appropriate log levels
- [ ] **Return results** as `Dict[str, Any]` with Decimal types
- [ ] **Add type hints** for all parameters and return values
- [ ] **Add docstrings** for all public methods

### **Service Verification**
```bash
# Verify Python syntax
python3 -m py_compile backend/app/services/<service_name>.py

# Test service method directly (optional)
python3 -c "
from backend.app.services.<service_name> import <ServiceClass>
import asyncio
service = <ServiceClass>()
result = asyncio.run(service.<method_name>(<test_args>))
print(result)
"
```

### **Service Best Practices**
- [ ] **Single Responsibility** - Each service has one clear purpose
- [ ] **Pure Functions** - No side effects, deterministic results
- [ ] **Error Handling** - Graceful degradation, not crashes
- [ ] **Logging** - Appropriate log levels (DEBUG, INFO, WARNING, ERROR)
- [ ] **Type Safety** - Use Decimal for financial data, proper types
- [ ] **Documentation** - Clear docstrings and comments

---

## 🤖 **AGENT IMPLEMENTATION CHECKLIST**

### **Agent Creation/Update**
- [ ] **Add capability to `get_capabilities()`** list
  ```python
  def get_capabilities(self) -> List[str]:
      return [
          "existing.capability",
          "new.capability",  # ADD THIS
      ]
  ```

- [ ] **Implement agent method** (convert dots to underscores)
  ```python
  async def new_capability(
      self,
      ctx: RequestCtx,
      state: Dict[str, Any],
      **kwargs
  ) -> Dict[str, Any]:
      """Capability description."""
      # Implementation here
      pass
  ```

### **Agent Method Implementation**
- [ ] **Method signature** follows BaseAgent pattern
- [ ] **Parameter validation** - Check required parameters
- [ ] **Service integration** - Call appropriate service methods
- [ ] **Error handling** - Catch and handle exceptions gracefully
- [ ] **Metadata attachment** - Attach AgentMetadata to results
- [ ] **Logging** - Log capability execution with context

### **Agent Verification**
```bash
# Verify Python syntax
python3 -m py_compile backend/app/agents/<agent_name>.py

# Test agent capability directly
python3 -c "
from backend.app.agents.<agent_name> import <AgentClass>
agent = <AgentClass>('test', {})
print(agent.get_capabilities())
"
```

### **Agent Best Practices**
- [ ] **Thin Agent, Fat Service** - Agents orchestrate, services implement
- [ ] **Consistent Naming** - Capability "foo.bar" → method "foo_bar"
- [ ] **Metadata Attachment** - Always attach metadata for traceability
- [ ] **RequestCtx Usage** - Use context for reproducibility
- [ ] **Graceful Degradation** - Handle missing services/data gracefully

---

## 🔗 **PATTERN INTEGRATION CHECKLIST**

### **Pattern Creation/Update**
- [ ] **Pattern JSON structure** follows schema
- [ ] **Capability references** use correct dot notation
- [ ] **Input validation** - Required inputs specified
- [ ] **Output mapping** - Clear output structure
- [ ] **Error handling** - Pattern-level error handling

### **Pattern Schema Compliance**
```json
{
  "id": "pattern_name",
  "name": "Human Readable Name",
  "version": "1.0.0",
  "category": "portfolio|macro|analysis|export",
  "inputs": {
    "required_param": {"type": "uuid", "required": true}
  },
  "outputs": ["output1", "output2"],
  "steps": [
    {
      "capability": "agent.capability",
      "args": {"param": "{{inputs.param}}"},
      "as": "result_name"
    }
  ],
  "rights_required": ["portfolio_read"],
  "export_allowed": {"pdf": true, "csv": true}
}
```

### **Pattern Verification**
```bash
# Test pattern execution
curl -X POST http://localhost:8000/v1/execute \
  -H "Content-Type: application/json" \
  -d '{
    "pattern_id": "pattern_name",
    "inputs": {"required_param": "test_value"}
  }'
```

---

## 🧪 **TESTING CHECKLIST**

### **Unit Tests**
- [ ] **Test all capabilities** - Each capability has unit tests
- [ ] **Test error scenarios** - Handle exceptions and edge cases
- [ ] **Test with mock data** - Use test fixtures and mocks
- [ ] **Test metadata attachment** - Verify metadata is attached
- [ ] **Test parameter validation** - Verify input validation

### **Integration Tests**
- [ ] **Test pattern execution** - End-to-end pattern testing
- [ ] **Test service integration** - Agent-service integration
- [ ] **Test database integration** - Database operations
- [ ] **Test error propagation** - Error handling across layers

### **Test File Structure**
```
backend/tests/
├── unit/
│   ├── test_<agent_name>.py
│   └── test_<service_name>.py
├── integration/
│   ├── test_pattern_execution.py
│   └── test_agent_integration.py
└── golden/
    └── test_<capability_name>.py
```

### **Test Execution**
```bash
# Run unit tests
pytest backend/tests/unit/test_<agent_name>.py -v

# Run integration tests
pytest backend/tests/integration/test_pattern_execution.py -v

# Run all tests with coverage
pytest backend/tests/ -v --cov=backend/app --cov-report=term
```

---

## 📊 **PERFORMANCE CHECKLIST**

### **Response Time Targets**
- [ ] **Simple capabilities** - < 100ms response time
- [ ] **Complex capabilities** - < 500ms response time
- [ ] **Database queries** - < 200ms response time
- [ ] **External API calls** - < 2s response time

### **Caching Strategy**
- [ ] **Appropriate TTL** - Set reasonable cache expiration
- [ ] **Cache invalidation** - Handle cache invalidation
- [ ] **Cache keys** - Use meaningful cache keys
- [ ] **Cache size limits** - Prevent memory issues

### **Performance Monitoring**
- [ ] **Response time logging** - Log capability execution times
- [ ] **Error rate monitoring** - Track error rates
- [ ] **Resource usage** - Monitor memory and CPU usage
- [ ] **Database performance** - Monitor query performance

---

## 🔒 **SECURITY CHECKLIST**

### **Input Validation**
- [ ] **Parameter validation** - Validate all inputs
- [ ] **Type checking** - Ensure correct data types
- [ ] **Range validation** - Check numeric ranges
- [ ] **Sanitization** - Sanitize user inputs

### **Access Control**
- [ ] **Rights checking** - Verify user permissions
- [ ] **RLS compliance** - Use Row-Level Security
- [ ] **Audit logging** - Log sensitive operations
- [ ] **Data filtering** - Filter sensitive data

### **Error Handling**
- [ ] **No information leakage** - Don't expose internal details
- [ ] **Graceful degradation** - Handle errors gracefully
- [ ] **Logging security** - Log security events
- [ ] **Exception handling** - Catch and handle exceptions

---

## 📝 **DOCUMENTATION CHECKLIST**

### **Agent Specification**
- [ ] **Create/update agent spec** - Document agent capabilities
- [ ] **Code examples** - Include implementation examples
- [ ] **Integration points** - Document service dependencies
- [ ] **Performance characteristics** - Document response times
- [ ] **Error handling** - Document error scenarios

### **Code Documentation**
- [ ] **Docstrings** - Document all public methods
- [ ] **Type hints** - Add type annotations
- [ ] **Comments** - Explain complex logic
- [ ] **README updates** - Update relevant README files

### **Documentation Verification**
- [ ] **Spec accuracy** - Verify spec matches implementation
- [ ] **Code examples** - Test all code examples
- [ ] **Link validation** - Check all links work
- [ ] **Grammar check** - Review for clarity and accuracy

---

## 🚀 **DEPLOYMENT CHECKLIST**

### **Pre-Deployment**
- [ ] **All tests pass** - Unit, integration, and golden tests
- [ ] **Performance benchmarks** - Meet performance targets
- [ ] **Security review** - Security checklist completed
- [ ] **Documentation complete** - All documentation updated

### **Deployment Steps**
- [ ] **Database migrations** - Apply any new migrations
- [ ] **Service restart** - Restart affected services
- [ ] **Health checks** - Verify service health
- [ ] **Monitoring** - Check monitoring dashboards

### **Post-Deployment**
- [ ] **Smoke tests** - Run basic functionality tests
- [ ] **Performance monitoring** - Monitor response times
- [ ] **Error monitoring** - Watch for errors
- [ ] **User feedback** - Monitor user feedback

---

## 🔄 **MAINTENANCE CHECKLIST**

### **Regular Maintenance**
- [ ] **Update dependencies** - Keep dependencies current
- [ ] **Review logs** - Check for errors and warnings
- [ ] **Performance review** - Monitor performance metrics
- [ ] **Security updates** - Apply security patches

### **Code Review**
- [ ] **Architecture compliance** - Follow DawsOS patterns
- [ ] **Code quality** - Maintain high code quality
- [ ] **Test coverage** - Ensure adequate test coverage
- [ ] **Documentation** - Keep documentation current

---

## 🎯 **SUCCESS CRITERIA**

### **Development Complete When**
- [ ] **All capabilities implemented** - Agent declares all capabilities
- [ ] **All tests pass** - Unit, integration, and golden tests
- [ ] **Performance targets met** - Response times within limits
- [ ] **Documentation complete** - Agent spec and code documented
- [ ] **Security review passed** - Security checklist completed
- [ ] **Code review approved** - Peer review completed

### **Production Ready When**
- [ ] **All patterns functional** - Patterns execute successfully
- [ ] **UI integration complete** - Frontend integration working
- [ ] **Monitoring in place** - Observability configured
- [ ] **Error handling robust** - Graceful error handling
- [ ] **Performance stable** - Consistent performance metrics

---

## 📞 **SUPPORT AND ESCALATION**

### **When to Escalate**
- **Architecture questions** - Contact ORCHESTRATOR
- **Service dependencies** - Contact service owner
- **Performance issues** - Contact INFRASTRUCTURE_ARCHITECT
- **Security concerns** - Contact security team

### **Resources**
- **Agent Specifications** - `.claude/agents/` directory
- **Implementation Matrix** - `IMPLEMENTATION_STATUS_MATRIX.md`
- **Architecture Guide** - `ORCHESTRATOR.md`
- **Product Spec** - `PRODUCT_SPEC.md`

---

## 🎉 **CONCLUSION**

This checklist ensures consistent, high-quality agent development following DawsOS best practices. Use it as a guide for all agent development work to maintain system quality and reliability.

**Remember**: Quality over speed. It's better to implement fewer capabilities well than many capabilities poorly.
