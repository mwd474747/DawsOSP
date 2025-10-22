"""
Streaming Execution Wrapper for Pattern Engine

Provides real-time progress updates as patterns execute steps,
integrating with Streamlit's native streaming support.
"""

from typing import Generator, Dict, Any, Optional
import time


class StreamingExecutor:
    """
    Wraps pattern execution to provide streaming progress updates.
    
    Yields incremental updates as each pattern step completes,
    allowing UI to show real-time progress.
    """
    
    def __init__(self, pattern_engine):
        """
        Initialize streaming executor.
        
        Args:
            pattern_engine: PatternEngine instance to wrap
        """
        self.pattern_engine = pattern_engine
    
    def execute_pattern_streaming(
        self,
        pattern_id: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Execute pattern with streaming updates.
        
        Yields progress updates as each step completes:
        - step_start: When a step begins
        - step_complete: When a step finishes
        - final_result: Complete pattern result
        
        Args:
            pattern_id: Pattern identifier
            params: Parameters for pattern execution
            context: Additional context (conversation memory, etc.)
            
        Yields:
            Progress update dicts with type and data
        """
        # Load pattern
        pattern = self.pattern_engine.patterns.get(pattern_id)
        if not pattern:
            yield {
                "type": "error",
                "message": f"Pattern not found: {pattern_id}",
                "timestamp": time.time()
            }
            return
        
        yield {
            "type": "pattern_start",
            "pattern_id": pattern_id,
            "pattern_name": pattern.get("name", pattern_id),
            "total_steps": len(pattern.get("steps", [])),
            "timestamp": time.time()
        }
        
        # Execute each step with progress updates
        steps = pattern.get("steps", [])
        step_results = {}
        
        for step_index, step in enumerate(steps, 1):
            # Announce step start
            step_description = step.get("description", f"Step {step_index}")
            capability = step.get("params", {}).get("capability", "Processing")
            
            yield {
                "type": "step_start",
                "step_number": step_index,
                "total_steps": len(steps),
                "description": step_description or f"Executing {capability}",
                "timestamp": time.time()
            }
            
            # Execute step (this could be async in the future)
            try:
                # Simplified step execution - in real implementation,
                # this would call the actual pattern engine step executor
                step_start = time.time()
                
                # Simulate step execution
                # In production, this would call:
                # result = self.pattern_engine._execute_step(step, params, step_results)
                result = {
                    "status": "completed",
                    "step": step_index,
                    "data": {}  # Actual step result would go here
                }
                
                step_duration = time.time() - step_start
                step_results[f"step_{step_index}"] = result
                
                yield {
                    "type": "step_complete",
                    "step_number": step_index,
                    "total_steps": len(steps),
                    "duration_seconds": step_duration,
                    "timestamp": time.time()
                }
                
            except Exception as e:
                yield {
                    "type": "step_error",
                    "step_number": step_index,
                    "error": str(e),
                    "timestamp": time.time()
                }
                # Continue or stop based on error handling config
                if pattern.get("error_handling") == "stop":
                    break
        
        # Return final result
        yield {
            "type": "pattern_complete",
            "pattern_id": pattern_id,
            "timestamp": time.time()
        }
        
        # Execute full pattern to get actual result
        # (In production, we'd accumulate step_results above)
        try:
            final_result = self.pattern_engine.execute_pattern(pattern_id, params)
            yield {
                "type": "final_result",
                "result": final_result,
                "timestamp": time.time()
            }
        except Exception as e:
            yield {
                "type": "execution_error",
                "error": str(e),
                "timestamp": time.time()
            }
    
    def execute_with_llm_streaming(
        self,
        pattern_id: str,
        params: Dict[str, Any],
        llm_step_index: Optional[int] = None
    ) -> Generator[str, None, None]:
        """
        Execute pattern with LLM response streaming.
        
        For patterns that have Claude/LLM steps, stream the LLM response
        token by token for better UX.
        
        Args:
            pattern_id: Pattern identifier
            params: Parameters for pattern execution
            llm_step_index: Which step generates LLM response (default: last step)
            
        Yields:
            LLM response chunks (text tokens)
        """
        # Load pattern
        pattern = self.pattern_engine.patterns.get(pattern_id)
        if not pattern:
            yield "Error: Pattern not found"
            return
        
        # Execute pattern steps before LLM
        steps = pattern.get("steps", [])
        if not steps:
            yield "Error: No steps in pattern"
            return
        
        # Determine which step is the LLM step
        if llm_step_index is None:
            llm_step_index = len(steps) - 1  # Default to last step
        
        # Execute preceding steps silently
        step_results = {}
        for i, step in enumerate(steps):
            if i < llm_step_index:
                # Execute non-LLM steps
                # In production: step_results[f"step_{i}"] = execute_step(step)
                pass
        
        # Stream LLM step
        llm_step = steps[llm_step_index]
        agent = llm_step.get("params", {}).get("agent")
        
        if agent == "claude":
            # Stream Claude response
            # In production, this would actually stream from Anthropic API
            # For now, simulate streaming
            sample_response = "Analysis in progress..."
            for chunk in sample_response.split():
                yield chunk + " "
                time.sleep(0.05)  # Simulate streaming delay
        else:
            # Non-streaming execution
            result = self.pattern_engine.execute_pattern(pattern_id, params)
            response = result.get("formatted_response", str(result))
            yield response


def format_progress_message(update: Dict[str, Any]) -> str:
    """
    Format streaming update for display.
    
    Args:
        update: Streaming update dict
        
    Returns:
        Formatted message string
    """
    update_type = update.get("type")
    
    if update_type == "pattern_start":
        return f"🔮 Starting {update['pattern_name']}..."
    
    elif update_type == "step_start":
        return f"⏳ Step {update['step_number']}/{update['total_steps']}: {update['description']}"
    
    elif update_type == "step_complete":
        duration = update.get("duration_seconds", 0)
        return f"✅ Step {update['step_number']}/{update['total_steps']} complete ({duration:.2f}s)"
    
    elif update_type == "step_error":
        return f"❌ Error in step {update['step_number']}: {update['error']}"
    
    elif update_type == "pattern_complete":
        return f"✨ {update['pattern_id']} complete!"
    
    elif update_type == "error":
        return f"❌ Error: {update['message']}"
    
    else:
        return ""
