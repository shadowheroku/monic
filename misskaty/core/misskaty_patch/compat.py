# misskayt_patch/compat.py
"""
Compatibility patch for MissKaty fork–specific features.
This allows the bot to run on stock Pyrogram without breaking.
"""

from pyrogram.errors import RPCError


# ============================
#  Error classes (MissKaty fork)
# ============================

class ChatSendPlainForbidden(RPCError):
    """MissKaty-only error: raised when plain messages are not allowed in a chat."""
    def __init__(self, message="ChatSendPlainForbidden: Plain messages not allowed"):
        super().__init__(message=message, code=400, x=None)


class TopicClosed(RPCError):
    """MissKaty-only error: raised when trying to send to a closed topic."""
    def __init__(self, message="TopicClosed: Topic is closed"):
        super().__init__(message=message, code=400, x=None)


# ============================
#  Extra flags / constants
# ============================

# MissKaty adds this param to control bandwidth
try:
    max_concurrent_transmissions = 5
except Exception:
    max_concurrent_transmissions = None


# ============================
#  Safe Import Helper
# ============================

def safe_import_patch(name: str):
    """
    Return a safe placeholder for MissKaty-specific imports.
    Example:
        from misskayt_patch.compat import safe_import_patch
        SomeClass = safe_import_patch("SomeClass")
    """
    class Dummy:
        def __init__(self, *a, **kw):
            raise RuntimeError(f"{name} is not supported in this Pyrogram build")

    return Dummy


__all__ = [
    "ChatSendPlainForbidden",
    "TopicClosed",
    "max_concurrent_transmissions",
    "safe_import_patch",
]
