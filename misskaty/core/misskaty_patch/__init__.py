from . import bound, decorators, methods

# --- Add MongoDB & compatibility patch for Pyrogram Client ---
from pyrogram import Client as PyroClient

# Backup original __init__
_original_init = PyroClient.__init__


def patched_init(self, *args, **kwargs):
    """
    Patch Pyrogram.Client to accept MissKaty-specific args without breaking.
    """

    # Handle MissKaty-only kwargs
    unsupported_keys = [
        "mongodb",
        "max_concurrent_transmissions",
        "max_concurrent_transmissions_limit",
    ]

    for key in unsupported_keys:
        if key in kwargs:
            setattr(self, key, kwargs.pop(key, None))

    # Handle `session_string` → convert to session_name (only if not already provided)
    if "session_string" in kwargs:
        session_string = kwargs.pop("session_string")
        setattr(self, "session_string", session_string)

        # Only inject session_name if neither positional args nor kwargs provided it
        has_positional_session = len(args) >= 1
        has_kw_session = "session_name" in kwargs

        if not has_positional_session and not has_kw_session:
            kwargs["session_name"] = session_string

    # Finally call the original Pyrogram Client
    _original_init(self, *args, **kwargs)


# Patch Pyrogram Client
PyroClient.__init__ = patched_init
