"""
app/schemas package: Pydantic models for request validation and response formatting.
"""

from app.schemas import (
    auth,
    contact,
    export,
    feedback,
    newsletter,
    subscription,
    subtitle,
    transcription,
    user,
)

__all__ = []

for module in (
    auth,
    user,
    subscription,
    transcription,
    subtitle,
    export,
    contact,
    newsletter,
    feedback,
):
    # only extend if this module defines its own __all__
    if hasattr(module, "__all__"):
        __all__.extend(module.__all__)
