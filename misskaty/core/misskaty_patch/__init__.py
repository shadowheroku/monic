from . import bound, decorators, methods

# --- Add MongoDB & compatibility patch for Pyrogram Client ---
from pyrogram import Client as PyroClient

# Backup original __init__
_original_init = PyroClient.__init__


def patched_init(self, *args, **kwargs):
    # MissKaty fork passed extra arguments not supported in official Pyrogram.
    # We just absorb & ignore them.
    unsupported_keys = [
        "mongodb",
        "max_concurrent_transmissions",  # MissKaty custom
        "max_concurrent_transmissions_limit",  # just in case
    ]

    for key in unsupported_keys:
        if key in kwargs:
            setattr(self, key, kwargs.pop(key, None))

    # Call the original Pyrogram Client.__init__
    _original_init(self, *args, **kwargs)


# Patch Pyrogram Client
PyroClient.__init__ = patched_init
