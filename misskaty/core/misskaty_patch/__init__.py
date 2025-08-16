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

    # Handle `session_string` → convert to session_name
    if "session_string" in kwargs:
        session_string = kwargs.pop("session_string")
        # Store it for later use if plugins expect it
        setattr(self, "session_string", session_string)

        # If no session_name provided, use session_string as session_name
        if "session_name" not in kwargs:
            kwargs["session_name"] = session_string

    # Finally call the original Pyrogram Client
    _original_init(self, *args, **kwargs)


# Patch Pyrogram Client
PyroClient.__init__ = patched_init
