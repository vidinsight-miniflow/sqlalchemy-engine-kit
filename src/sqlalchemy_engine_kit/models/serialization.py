"""
Model Serialization Utilities

This module provides utilities for converting SQLAlchemy models to dictionaries
and JSON strings, useful for API responses and data serialization.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
from enum import Enum
import json


def _serialize_value(value: Any) -> Any:
    """Serialize a single value to JSON-serializable format.
    
    Args:
        value: Value to serialize
    
    Returns:
        JSON-serializable value
    """
    if value is None:
        return None
    
    # Primitif tipler - en sık karşılaşılan
    if isinstance(value, (str, int, float, bool)):
        return value
    
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    
    if isinstance(value, Decimal):
        return float(value)
    
    if isinstance(value, UUID):
        return str(value)
    
    if isinstance(value, Enum):
        return value.value
    
    if isinstance(value, bytes):
        return value.decode('utf-8', errors='ignore')
    
    if isinstance(value, (list, dict)):
        return value
    
    if isinstance(value, (set, frozenset)):
        return list(value)
    
    if hasattr(value, '__dict__'):
        return str(value)
    
    return value


def _json_serializer(obj: Any) -> Any:
    """Custom JSON serializer for json.dumps default parameter.
    
    Args:
        obj: Object to serialize
    
    Returns:
        JSON-serializable value
    
    Raises:
        TypeError: If object cannot be serialized
    """
    result = _serialize_value(obj)
    
    if result is obj and not isinstance(obj, (str, int, float, bool, list, dict, type(None))):
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    return result


def model_to_dict(
    instance: Any,
    exclude: Optional[List[str]] = None,
    include_relationships: bool = False,
    max_depth: int = 1,
    _exclude_set: Optional[set] = None
) -> Dict[str, Any]:
    """Convert SQLAlchemy model instance to dictionary.
    
    Converts a SQLAlchemy model instance to a Python dictionary, handling
    common data types like datetime, date, Decimal, UUID, Enum, and relationships.
    
    Args:
        instance: SQLAlchemy model instance
        exclude: List of field names to exclude from output
        include_relationships: If True, include relationship data (default: False)
        max_depth: Maximum depth for relationship serialization (default: 1)
        _exclude_set: Internal parameter for optimization (do not use directly)
    
    Returns:
        Dict[str, Any]: Dictionary representation of the model
    
    Raises:
        ValueError: If instance is None
    
    Examples:
        >>> from engine_kit.models.serialization import model_to_dict
        >>> 
        >>> user = User(id=1, email="test@example.com", name="Test User")
        >>> user_dict = model_to_dict(user)
        >>> # {'id': 1, 'email': 'test@example.com', 'name': 'Test User'}
        
        >>> # Exclude sensitive fields
        >>> user_dict = model_to_dict(user, exclude=['password', 'api_key'])
        
        >>> # Include relationships
        >>> user_dict = model_to_dict(user, include_relationships=True)
        >>> # Includes 'posts', 'comments', etc. if defined as relationships
    
    Note:
        - Handles datetime, date, Decimal, UUID, Enum, and other common types
        - Relationships are serialized as dictionaries if include_relationships=True
        - Circular references are prevented by max_depth parameter
        - Excludes SQLAlchemy internal attributes (starting with _)
    """
    if instance is None:
        raise ValueError("Instance cannot be None")
    
    if _exclude_set is None:
        _exclude_set = set(exclude or [])
        _exclude_set.add('_sa_instance_state')
    
    result = {}
    
    table = getattr(instance, '__table__', None)
    if table is not None:
        for column in table.columns:
            column_name = column.name
            
            if column_name in _exclude_set or column_name.startswith('_'):
                continue
            
            value = getattr(instance, column_name, None)
            result[column_name] = _serialize_value(value)
    
    if include_relationships:
        mapper = getattr(instance, '__mapper__', None)
        if mapper is not None:
            for relationship in mapper.relationships:
                rel_name = relationship.key
                
                if rel_name in _exclude_set:
                    continue
                
                rel_value = getattr(instance, rel_name, None)
                
                if rel_value is None:
                    result[rel_name] = None
                elif isinstance(rel_value, list):
                    if max_depth > 0:
                        result[rel_name] = [
                            model_to_dict(
                                item,
                                include_relationships=False,
                                max_depth=max_depth - 1,
                                _exclude_set=_exclude_set
                            )
                            for item in rel_value
                        ]
                    else:
                        result[rel_name] = []
                else:
                    if max_depth > 0:
                        result[rel_name] = model_to_dict(
                            rel_value,
                            include_relationships=False,
                            max_depth=max_depth - 1,
                            _exclude_set=_exclude_set
                        )
                    else:
                        result[rel_name] = None
    
    return result


def models_to_list(
    instances: Optional[List[Any]],
    exclude: Optional[List[str]] = None,
    include_relationships: bool = False
) -> List[Dict[str, Any]]:
    """Convert list of SQLAlchemy model instances to list of dictionaries.
    
    Convenience function for serializing multiple model instances.
    
    Args:
        instances: List of SQLAlchemy model instances
        exclude: List of field names to exclude from output
        include_relationships: If True, include relationship data (default: False)
    
    Returns:
        List[Dict[str, Any]]: List of dictionary representations
    
    Examples:
        >>> from engine_kit.models.serialization import models_to_list
        >>> 
        >>> users = [User(id=1, email="user1@example.com"), User(id=2, email="user2@example.com")]
        >>> users_list = models_to_list(users)
        >>> # [{'id': 1, 'email': 'user1@example.com'}, {'id': 2, 'email': 'user2@example.com'}]
        
        >>> # Exclude fields
        >>> users_list = models_to_list(users, exclude=['password'])
        
        >>> # Handle empty list
        >>> empty_list = models_to_list([])
        >>> # []
    """
    if not instances:
        return []
    
    exclude_set = set(exclude or [])
    exclude_set.add('_sa_instance_state')
    
    return [
        model_to_dict(
            instance,
            include_relationships=include_relationships,
            _exclude_set=exclude_set
        )
        for instance in instances
    ]


def model_to_json(
    instance: Any,
    exclude: Optional[List[str]] = None,
    include_relationships: bool = False,
    indent: Optional[int] = None,
    ensure_ascii: bool = False
) -> str:
    """Convert SQLAlchemy model instance to JSON string.
    
    Converts a SQLAlchemy model instance to a JSON string, handling
    common data types like datetime, date, Decimal, UUID, and Enum.
    
    Args:
        instance: SQLAlchemy model instance
        exclude: List of field names to exclude from output
        include_relationships: If True, include relationship data (default: False)
        indent: JSON indentation level (None for compact, 2 for pretty)
        ensure_ascii: If True, escape non-ASCII characters (default: False)
    
    Returns:
        str: JSON string representation of the model
    
    Examples:
        >>> from engine_kit.models.serialization import model_to_json
        >>> 
        >>> user = User(id=1, email="test@example.com", name="Test User")
        >>> json_str = model_to_json(user)
        >>> # '{"id": 1, "email": "test@example.com", "name": "Test User"}'
        
        >>> # Pretty print
        >>> json_str = model_to_json(user, indent=2)
        
        >>> # Exclude sensitive fields
        >>> json_str = model_to_json(user, exclude=['password'])
    
    Note:
        - Handles datetime, date, Decimal, UUID, Enum serialization
        - Uses custom JSON encoder for non-standard types
        - Suitable for API responses
    """
    exclude_set = set(exclude or [])
    exclude_set.add('_sa_instance_state')
    
    data = model_to_dict(
        instance,
        include_relationships=include_relationships,
        _exclude_set=exclude_set
    )
    
    return json.dumps(
        data,
        indent=indent,
        ensure_ascii=ensure_ascii,
        default=_json_serializer
    )