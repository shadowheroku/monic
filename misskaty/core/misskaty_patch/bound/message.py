import html
import io
from asyncio import get_event_loop
from asyncio import sleep as asleep
from logging import getLogger
from typing import Union

from pyrogram.errors import (
    ChannelPrivate,
    ChatAdminRequired,
    ChatWriteForbidden,
    FloodWait,
    MessageAuthorRequired,
    MessageDeleteForbidden,
    MessageIdInvalid,
    MessageNotModified,
    MessageTooLong,
    Forbidden,
)

# --- Compatibility patches for MissKaty fork ---
class ChatSendPlainForbidden(Forbidden):
    """Backwards compatibility: MissKaty expected this error class."""
    pass

class TopicClosed(Forbidden):
    """Backwards compatibility: raised when replying to a closed forum topic."""
    pass

from pyrogram.types import Message

LOGGER = getLogger("MissKaty")


@property
def parse_cmd(msg):
    return msg.text.split(None, 1)[1] if len(msg.command) > 1 else None


# --- Message helpers ---
async def reply_text(
    self: Message, text: str, as_raw: bool = False, del_in: int = 0, *args, **kwargs
) -> Union["Message", bool]:
    try:
        if as_raw:
            msg = await self.reply_text(
                text=f"<code>{html.escape(text)}</code>", *args, **kwargs
            )
        else:
            msg = await self.reply_text(text=text, *args, **kwargs)

        if del_in == 0:
            return msg
        await asleep(del_in)
        return bool(await msg.delete_msg())
    except FloodWait as e:
        LOGGER.warning(f"Got floodwait in {self.chat.id} for {e.value}'s.")
        await asleep(e.value)
        return await reply_text(self, text, *args, **kwargs)
    except (TopicClosed, ChannelPrivate):
        return
    except (ChatWriteForbidden, ChatAdminRequired, ChatSendPlainForbidden):
        chat_title = getattr(self.chat, "title", getattr(self.chat, "first_name", self.chat.id))
        LOGGER.info(f"Leaving from {chat_title} [{self.chat.id}] due to insufficient permissions.")
        return await self.chat.leave()


async def edit_text(
    self: Message, text: str, del_in: int = 0, *args, **kwargs
) -> Union["Message", bool]:
    try:
        msg = await self.edit_text(text, *args, **kwargs)
        if del_in == 0:
            return msg
        await asleep(del_in)
        return bool(await msg.delete_msg())
    except FloodWait as e:
        LOGGER.warning(f"Got floodwait in {self.chat.id} for {e.value}'s.")
        await asleep(e.value)
        return await edit_text(self, text, *args, **kwargs)
    except (MessageNotModified, ChannelPrivate):
        return False
    except (ChatWriteForbidden, ChatAdminRequired):
        chat_title = getattr(self.chat, "title", getattr(self.chat, "first_name", self.chat.id))
        LOGGER.info(f"Leaving from {chat_title} [{self.chat.id}] due to insufficient permissions.")
        return await self.chat.leave()
    except (MessageAuthorRequired, MessageIdInvalid):
        return await reply_text(self, text=text, *args, **kwargs)


async def edit_or_send_as_file(
    self: Message, text: str, del_in: int = 0, as_raw: bool = False, *args, **kwargs
) -> Union["Message", bool]:
    text = html.escape(text) if as_raw else text
    try:
        msg = await edit_text(self, text=text, *args, **kwargs)
        if del_in == 0:
            return msg
        await asleep(del_in)
        return bool(await msg.delete_msg())
    except (MessageTooLong, OSError):
        return await reply_as_file(self, text=text, *args, **kwargs)


async def reply_or_send_as_file(
    self: Message, text: str, as_raw: bool = False, del_in: int = 0, *args, **kwargs
) -> Union["Message", bool]:
    text = html.escape(text) if as_raw else text
    try:
        return await reply_text(self, text=text, del_in=del_in, *args, **kwargs)
    except MessageTooLong:
        return await reply_as_file(self, text=text, **kwargs)


async def reply_as_file(
    self: Message,
    text: str,
    filename: str = "output.txt",
    caption: str = "",
    delete_message: bool = True,
):
    reply_to_id = self.reply_to_message.id if self.reply_to_message else self.id
    if delete_message:
        get_event_loop().create_task(self.delete())
    doc = io.BytesIO(text.encode())
    doc.name = filename
    return await self.reply_document(
        document=doc,
        caption=caption[:1024],
        disable_notification=True,
        reply_to_message_id=reply_to_id,
    )


async def delete(self: Message, revoke: bool = True) -> bool:
    try:
        return bool(await self.delete(revoke=revoke))
    except FloodWait as e:
        LOGGER.warning(str(e))
        await asleep(e.value)
        return await delete(self, revoke)
    except MessageDeleteForbidden:
        return False
    except Exception as e:
        LOGGER.warning(str(e))


# --- Monkey-patch methods onto Message ---
Message.reply_msg = reply_text
Message.edit_msg = edit_text
Message.edit_or_send_as_file = edit_or_send_as_file
Message.reply_or_send_as_file = reply_or_send_as_file
Message.reply_as_file = reply_as_file
Message.delete_msg = delete
Message.input = parse_cmd
