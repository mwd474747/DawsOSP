# workflows/workflow_engine.py
class WorkflowRecorder:
    def __init__(self):
        self.workflows = []
        self.load_existing()
    
    def record(self, trigger, actions, results):
        """Every successful interaction becomes a reusable workflow"""
        workflow = {
            'id': f"workflow_{datetime.now().timestamp()}",
            'trigger': trigger,
            'actions': actions,
            'results': results,
            'success_rate': 1.0,
            'uses': 1,
            'created': datetime.now().isoformat()
        }
        self.workflows.append(workflow)
        self._identify_pattern(workflow)
        
    def _identify_pattern(self, workflow):
        """After 3+ similar workflows, create a pattern"""
        similar = self._find_similar(workflow)
        if len(similar) >= 3:
            pattern = {
                'name': self._generate_pattern_name(workflow),
                'template': self._extract_template(similar),
                'success_rate': self._calculate_success(similar)
            }
            self.save_pattern(pattern)
            
    def find_applicable(self, context):
        """Find workflows that might apply to current context"""
        applicable = []
        for workflow in self.workflows:
            if self._matches_context(workflow, context):
                applicable.append(workflow)
        return sorted(applicable, key=lambda w: w['success_rate'], reverse=True)