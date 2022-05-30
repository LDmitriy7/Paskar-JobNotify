import asyncio
import functools
from sys import exc_info

from aiogram import types, exceptions

from app import logger, bot


def bot_error_handler(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # noinspection PyBroadException
        try:
            ret = await func(*args, **kwargs)
        except exceptions.BotBlocked:
            logger.warning(f"{func.__name__}: bot blocked in chat, {args}")
        except exceptions.BotKicked:
            logger.warning(f"{func.__name__}: bot kicked from the chat, {args}")
        except exceptions.ChatAdminRequired:
            logger.warning(f"{func.__name__}: not sufficient permissions, {args}")
        except exceptions.RetryAfter as e:
            logger.warning(f"{func.__name__}: Flood limit exceeded. Sleep {e.timeout} seconds")
            await asyncio.sleep(e.timeout)
            return await func(*args, **kwargs)
        except exceptions.UserDeactivated:
            logger.warning(f"{func.__name__}: user is deactivated, {args}")
        except exceptions.Unauthorized:
            logger.error(f"{func.__name__}: Unauthorized, {args}, {exc_info()}")
        except exceptions.TelegramAPIError:
            logger.error(f"{func.__name__}: telegram API error, {args}, {exc_info()}")
        except Exception:
            logger.error(f"{func.__name__}: Unknown exception, {exc_info()}")
        else:
            return ret
        return None

    return wrapper


@bot_error_handler
async def send_message(user_id: int, text: str, reply_msg_id: int = 0, disable_notification: bool = False,
                       parse_mode: types.ParseMode = None, reply_markup=None) -> types.Message:
    if reply_msg_id:
        return await bot.send_message(user_id, text, reply_to_message_id=reply_msg_id,
                                      disable_notification=disable_notification, parse_mode=parse_mode,
                                      reply_markup=reply_markup)
    else:
        return await bot.send_message(user_id, text, disable_notification=disable_notification, parse_mode=parse_mode,
                                      reply_markup=reply_markup)


@bot_error_handler
async def restrict_write(group_id: int, user_id: int, until_time: int = 0, _unrestrict: bool = False):
    perms = types.ChatPermissions(can_send_messages=_unrestrict)
    await bot.restrict_chat_member(group_id, user_id, permissions=perms, until_date=until_time)


@bot_error_handler
async def unrestrict(group_id: int, user_id: int, until_time: int = 0, _unrestrict: bool = False):
    perms = types.ChatPermissions(can_send_messages=True, can_send_polls=True, can_send_media_messages=True,
                                  can_send_other_messages=True, can_add_web_page_previews=True,
                                  can_change_info=True, can_invite_users=True, can_pin_messages=True)
    await bot.restrict_chat_member(group_id, user_id, permissions=perms, until_date=until_time)


@bot_error_handler
async def get_chat_member(group_id, user_id):
    await bot.get_chat_member(group_id, user_id)


@bot_error_handler
async def kick_member(group_id, user_id):
    await bot.kick_chat_member(group_id, user_id)


@bot_error_handler
async def unban_member(group_id, user_id):
    await bot.unban_chat_member(group_id, user_id)


@bot_error_handler
async def export_link(group_id):
    return await bot.export_chat_invite_link(group_id)


@bot_error_handler
async def edit_message(text, chat_id, message_id, parse_mode=None, reply_markup=None):
    return await bot.edit_message_text(text, chat_id, message_id, parse_mode=parse_mode, reply_markup=reply_markup)


@bot_error_handler
async def edit_message_reply_markup(chat_id, message_id, reply_markup):
    return await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=reply_markup)
