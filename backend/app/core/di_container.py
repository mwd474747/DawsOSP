"""
Dependency Injection Container

Purpose: Manage service initialization and dependency injection
Updated: 2025-01-15
Priority: P0 (Critical for Phase 2)

Features:
    - Service registration and resolution
    - Dependency order management
    - Lazy initialization
    - Type-safe service access

Usage:
    container = DIContainer()
    container.register("db_pool", db_pool)
    container.register_service("pricing", PricingService, db_pool="db_pool")
    pricing_service = container.resolve("pricing")
"""

import logging
from typing import Any, Dict, Optional, Type, Callable, TypeVar, Generic
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceLifetime(Enum):
    """Service lifetime options."""
    SINGLETON = "singleton"  # One instance per container
    TRANSIENT = "transient"  # New instance each time
    SCOPED = "scoped"  # One instance per request scope


class ServiceRegistration:
    """Service registration metadata."""
    
    def __init__(
        self,
        service_type: Type[T],
        factory: Optional[Callable[..., T]] = None,
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
        dependencies: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize service registration.
        
        Args:
            service_type: Service class type
            factory: Factory function (optional, uses service_type if not provided)
            lifetime: Service lifetime (default: SINGLETON)
            dependencies: Dependency mapping {param_name: service_key}
        """
        self.service_type = service_type
        self.factory = factory or service_type
        self.lifetime = lifetime
        self.dependencies = dependencies or {}
        self.instance: Optional[T] = None


class DIContainer:
    """
    Dependency injection container.
    
    Manages service registration, resolution, and lifecycle.
    """
    
    def __init__(self):
        """Initialize DI container."""
        self._services: Dict[str, ServiceRegistration] = {}
        self._instances: Dict[str, Any] = {}  # Singleton instances
        self._initialized: bool = False
    
    def register(
        self,
        key: str,
        instance: Any,
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
    ) -> None:
        """
        Register an existing instance.
        
        Args:
            key: Service key
            instance: Service instance
            lifetime: Service lifetime (default: SINGLETON)
        """
        if key in self._services:
            logger.warning(f"Service '{key}' already registered, overwriting")
        
        # Create a dummy registration for existing instances
        registration = ServiceRegistration(
            service_type=type(instance),
            factory=lambda: instance,
            lifetime=lifetime,
        )
        registration.instance = instance
        self._services[key] = registration
        
        if lifetime == ServiceLifetime.SINGLETON:
            self._instances[key] = instance
    
    def register_service(
        self,
        key: str,
        service_type: Type[T],
        factory: Optional[Callable[..., T]] = None,
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
        **dependencies: str,
    ) -> None:
        """
        Register a service type.
        
        Args:
            key: Service key
            service_type: Service class type
            factory: Factory function (optional)
            lifetime: Service lifetime (default: SINGLETON)
            **dependencies: Dependency mapping {param_name: service_key}
        
        Example:
            container.register_service(
                "pricing",
                PricingService,
                db_pool="db_pool",
            )
        """
        if key in self._services:
            logger.warning(f"Service '{key}' already registered, overwriting")
        
        registration = ServiceRegistration(
            service_type=service_type,
            factory=factory or service_type,
            lifetime=lifetime,
            dependencies=dependencies,
        )
        self._services[key] = registration
    
    def resolve(self, key: str) -> Any:
        """
        Resolve a service instance.
        
        Args:
            key: Service key
        
        Returns:
            Service instance
        
        Raises:
            KeyError: If service not registered
            RuntimeError: If dependency resolution fails
        """
        if key not in self._services:
            raise KeyError(f"Service '{key}' not registered")
        
        registration = self._services[key]
        
        # Return singleton instance if exists
        if registration.lifetime == ServiceLifetime.SINGLETON:
            if key in self._instances:
                return self._instances[key]
        
        # Resolve dependencies
        resolved_deps = {}
        for param_name, dep_key in registration.dependencies.items():
            try:
                resolved_deps[param_name] = self.resolve(dep_key)
            except KeyError as e:
                raise RuntimeError(
                    f"Failed to resolve dependency '{dep_key}' for service '{key}': {e}"
                )
        
        # Create instance
        try:
            instance = registration.factory(**resolved_deps)
        except Exception as e:
            raise RuntimeError(
                f"Failed to create instance of '{key}': {e}"
            )
        
        # Store singleton instance
        if registration.lifetime == ServiceLifetime.SINGLETON:
            self._instances[key] = instance
            registration.instance = instance
        
        return instance
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a service instance (with default).
        
        Args:
            key: Service key
            default: Default value if not found
        
        Returns:
            Service instance or default
        """
        try:
            return self.resolve(key)
        except (KeyError, RuntimeError):
            return default
    
    def is_registered(self, key: str) -> bool:
        """Check if service is registered."""
        return key in self._services
    
    def clear(self) -> None:
        """Clear all registrations and instances."""
        self._services.clear()
        self._instances.clear()
        self._initialized = False
    
    def initialize_services(self, dependency_order: Optional[list] = None) -> None:
        """
        Initialize all services in dependency order.
        
        Args:
            dependency_order: Optional list of service keys in initialization order
        """
        if self._initialized:
            logger.warning("Services already initialized")
            return
        
        if dependency_order:
            # Initialize in specified order
            for key in dependency_order:
                if key in self._services:
                    try:
                        self.resolve(key)
                        logger.debug(f"Initialized service: {key}")
                    except Exception as e:
                        logger.error(f"Failed to initialize service '{key}': {e}")
                        raise
        else:
            # Initialize all services
            for key in self._services:
                try:
                    self.resolve(key)
                    logger.debug(f"Initialized service: {key}")
                except Exception as e:
                    logger.error(f"Failed to initialize service '{key}': {e}")
                    raise
        
        self._initialized = True
        logger.info(f"Initialized {len(self._instances)} services")


# Global container instance
_container: Optional[DIContainer] = None


def get_container() -> DIContainer:
    """Get global DI container instance."""
    global _container
    if _container is None:
        _container = DIContainer()
    return _container


def reset_container() -> None:
    """Reset global DI container (for testing)."""
    global _container
    _container = None

