from . import bound, decorators, methods

# --- Add MongoDB patch for Pyrogram Client ---
from pyrogram import Client as PyroClient

# Backup original __init__
_original_init = PyroClient.__init__

def patched_init(self, *args, **kwargs):
    # Handle mongodb argument if provided
    self.mongodb = kwargs.pop("mongodb", None)
    _original_init(self, *args, **kwargs)

# Patch Pyrogram Client
PyroClient.__init__ = patched_init
