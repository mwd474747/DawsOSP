"""
Logging system for DawsOS
Provides structured logging with different levels and output formats
"""
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

class DawsOSLogger:
    """Custom logger for DawsOS with structured logging support"""

    def __init__(self, name: str = 'DawsOS', log_dir: str = 'logs'):
        """
        Initialize logger

        Args:
            name: Logger name
            log_dir: Directory for log files
        """
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Remove existing handlers
        self.logger.handlers = []

        # File handler for all logs
        log_file = self.log_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)

        # Error file handler
        error_file = self.log_dir / f"{name}_errors_{datetime.now().strftime('%Y%m%d')}.log"
        error_handler = logging.FileHandler(error_file)
        error_handler.setLevel(logging.ERROR)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )

        file_handler.setFormatter(detailed_formatter)
        error_handler.setFormatter(detailed_formatter)
        console_handler.setFormatter(simple_formatter)

        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)

        # Metrics tracking
        self.metrics = {
            'api_calls': 0,
            'pattern_matches': 0,
            'errors': 0,
            'warnings': 0,
            'agent_executions': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }

    def debug(self, message: str, **kwargs):
        """Debug level logging"""
        extra = json.dumps(kwargs) if kwargs else ""
        self.logger.debug(f"{message} {extra}")

    def info(self, message: str, **kwargs):
        """Info level logging"""
        extra = json.dumps(kwargs) if kwargs else ""
        self.logger.info(f"{message} {extra}")

    def warning(self, message: str, **kwargs):
        """Warning level logging"""
        self.metrics['warnings'] += 1
        extra = json.dumps(kwargs) if kwargs else ""
        self.logger.warning(f"{message} {extra}")

    def error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Error level logging"""
        self.metrics['errors'] += 1
        error_details = {
            'error_type': type(error).__name__ if error else None,
            'error_message': str(error) if error else None,
            **kwargs
        }
        extra = json.dumps(error_details)
        self.logger.error(f"{message} {extra}")

    def log_api_call(self, service: str, endpoint: str, success: bool, duration: float = 0, **kwargs):
        """Log API call with metrics"""
        self.metrics['api_calls'] += 1
        self.info(
            f"API Call: {service}",
            service=service,
            endpoint=endpoint,
            success=success,
            duration=duration,
            **kwargs
        )

    def log_pattern_match(self, pattern_id: str, confidence: float, matched: bool):
        """Log pattern matching attempt"""
        if matched:
            self.metrics['pattern_matches'] += 1
        self.debug(
            f"Pattern match: {pattern_id}",
            pattern_id=pattern_id,
            confidence=confidence,
            matched=matched
        )

    def log_agent_execution(self, agent: str, context: Dict[str, Any], result: Dict[str, Any], duration: float = 0):
        """Log agent execution"""
        self.metrics['agent_executions'] += 1
        self.info(
            f"Agent executed: {agent}",
            agent=agent,
            duration=duration,
            success='error' not in result
        )

    def log_cache(self, key: str, hit: bool):
        """Log cache access"""
        if hit:
            self.metrics['cache_hits'] += 1
        else:
            self.metrics['cache_misses'] += 1
        self.debug(f"Cache {'hit' if hit else 'miss'}: {key}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return {
            **self.metrics,
            'cache_hit_rate': self.metrics['cache_hits'] / max(1, self.metrics['cache_hits'] + self.metrics['cache_misses'])
        }

    def write_metrics(self):
        """Write metrics to file"""
        metrics_file = self.log_dir / f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(metrics_file, 'w') as f:
            json.dump(self.get_metrics(), f, indent=2)

# Global logger instance
logger = DawsOSLogger()

def get_logger(name: Optional[str] = None) -> DawsOSLogger:
    """Get logger instance"""
    if name:
        return DawsOSLogger(name)
    return logger