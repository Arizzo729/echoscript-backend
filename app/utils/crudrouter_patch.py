from typing import get_origin, get_args
import fastapi_crudrouter.core._utils as _utils

# Monkey-patch get_pk_type to support Pydantic v2

def patched_get_pk_type(schema, pk_field: str) -> type:
    """
    Determine the primary key type for Pydantic v2 schemas.
    Falls back to 'outer_type_' if annotation is unavailable.
    """
    field = schema.__fields__[pk_field]
    annotation = getattr(field, "annotation", None)

    if annotation is not None:
        origin = get_origin(annotation)
        if origin is None:
            return annotation
        args = get_args(annotation)
        return args[0] if args else origin

    return getattr(field, "outer_type_", None)

# Apply patch
_utils.get_pk_type = patched_get_pk_type