import re
from io import BytesIO

from i18n import t
from openpyxl import Workbook
from openpyxl.writer.excel import save_virtual_workbook

import config
import keyboards
from app import users
from safecalls import *

restricted_chars = ['_', '`', '*']


def parse_num(num: str):
    res = re.sub(r'\D', '', num)
    match = re.fullmatch(r'(38)?(?P<opcode>\d{3})(?P<gr1>\d{3})(?P<gr2>\d{2})(?P<gr3>\d{2})', res)
    if not match:
        return None
    else:
        return f'+38 {match.group("opcode")} {match.group("gr1")} {match.group("gr2")} {match.group("gr3")}'


class Stages:
    user_data = 0
    info = 1
    edit = 2
    tech_support = 3
    broadcast = 4


class PStages:
    name = 0
    sex = 1
    birthday = 2
    phone = 3
    city = 4
    vac = 5


def is_privchat(message: types.Message):
    return message.chat.type == types.chat.ChatType.PRIVATE


async def get_name(message: types.Message, user):
    if len(message.text) > 50:
        return await send_message(message.from_user.id, t('TOO_LONG_50', locale=user['lang']),
                                  reply_msg_id=message.message_id)

    text = message.text
    for char in restricted_chars:
        text = text.replace(char, '')

    if user['stage'] == Stages.edit:
        await users.find_one_and_update({'uid': message.from_user.id}, {'$set': {'name': text, 'stage': Stages.info}})
        await send_message(message.from_user.id, t('CHANGED_CHOOSE_ACTION', locale=user['lang']),
                           reply_markup=keyboards.get_user_keyboard(user['lang']) if user[
                                                                                         'uid'] not in config.ADMINS else
                           keyboards.get_admuser_keyboard(user['lang']))
    else:
        await users.find_one_and_update({'uid': message.from_user.id}, {'$set': {'name': text},
                                                                        '$inc': {'p_stage': 1}})
        await send_message(message.from_user.id, t('CHOOSE_SEX', locale=user['lang']),
                           reply_markup=keyboards.get_sex_keyboard(user['lang']))


async def get_phone(message: types.Message, user):
    if len(message.text) > 50:
        return await send_message(message.from_user.id, t('TOO_LONG_50', locale=user['lang']),
                                  reply_msg_id=message.message_id)

    text = message.text
    for char in restricted_chars:
        text = text.replace(char, '')

    text = parse_num(text)

    if text is None:
        return await send_message(message.from_user.id,
                                  t('INVALID_PHONE', locale=user['lang']))

    if user['stage'] == Stages.edit:
        await users.find_one_and_update({'uid': message.from_user.id}, {'$set': {'phone': text, 'stage': Stages.info}})
        await send_message(message.from_user.id, t('CHANGED_CHOOSE_ACTION', locale=user['lang']),
                           reply_markup=keyboards.get_user_keyboard(user['lang']) if user[
                                                                                         'uid'] not in config.ADMINS else
                           keyboards.get_admuser_keyboard(user['lang']))
    else:
        await users.find_one_and_update({'uid': message.from_user.id}, {'$set': {'phone': text},
                                                                        '$inc': {'p_stage': 1}})
        await send_message(message.from_user.id, t('CHOOSE_CITY', locale=user['lang']),
                           reply_markup=keyboards.get_places_keyboard())


async def get_birthday(message: types.Message, user):
    if len(message.text) > 20:
        return await send_message(message.from_user.id, t('TOO_LONG_20', locale=user['lang']),
                                  reply_msg_id=message.message_id)

    text = message.text
    for char in restricted_chars:
        text = text.replace(char, '')

    full_date = re.fullmatch(r'^(?P<date>0[1-9]|[12]\d|3[01])[- /.](?P<month>0[1-9]|1[012])'
                             r'[- /.](?P<decade>19|20)?(?P<year>\d\d)$',
                             text)
    if full_date is None:
        return await send_message(message.from_user.id, t('INVALID_DATE_FORMAT', locale=user['lang']))

    date = full_date.group('date')
    month = full_date.group('month')
    year = full_date.group('year')
    decade = full_date.group('decade') or ('20' if int(year) < 21 else '19')

    if user['stage'] == Stages.edit:
        await users.find_one_and_update({'uid': message.from_user.id},
                                        {'$set': {'date': date, 'month': month, 'decade': decade,
                                                  'year': year, 'stage': Stages.info}})
        await send_message(message.from_user.id, t('CHANGED_CHOOSE_ACTION', locale=user['lang']),
                           reply_markup=keyboards.get_user_keyboard(user['lang']) if user[
                                                                                         'uid'] not in config.ADMINS else
                           keyboards.get_admuser_keyboard(user['lang']))
    else:
        await users.find_one_and_update({'uid': message.from_user.id},
                                        {'$set': {'date': date, 'month': month, 'decade': decade,
                                                  'year': year}, '$inc': {'p_stage': 1}})
        await send_message(message.from_user.id,
                           t('CHOOSE_PHONE', locale=user['lang']))


async def get_vacs(message: types.Message, user):
    vacs = list(map(lambda x: x.strip(), message.text.lower().split(',')))
    await users.find_one_and_update({'uid': user['uid']}, {'$set': {'checks': vacs, 'stage': Stages.info}})
    # await users.find_one_and_update({'uid': query.from_user.id}, {'$set': {'stage': Stages.info}})
    await send_message(user['uid'], text=t('SUCCESS_REGISTERED', locale=user['lang']),
                       reply_markup=keyboards.get_user_keyboard(user['lang']) if user['uid'] not in config.ADMINS else
                       keyboards.get_admuser_keyboard(user['lang']))


async def text_message_handler(message: types.Message):
    if is_privchat(message):
        user = await users.find_one({'uid': message.from_user.id})
        if user is None:
            return await send_welcome_handler(message)

        if user['stage'] == Stages.broadcast:
            return await broadcast_handler(message)

        if user['stage'] == Stages.user_data or user['stage'] == Stages.edit:
            if user['p_stage'] == PStages.name:
                await get_name(message, user)
            if user['p_stage'] == PStages.birthday:
                await get_birthday(message, user)
            if user['p_stage'] == PStages.phone:
                await get_phone(message, user)
            if user['p_stage'] == PStages.vac:
                await get_vacs(message, user)

        elif user['stage'] == Stages.tech_support:
            await bot.send_message(config.TECHSUPPORT_CHAT_ID, f"[Сообщение от {message.from_user.full_name}"
                                                               f":]"
                                                               f"(tg://user?id={message.from_user.id})",
                                   parse_mode=types.ParseMode.MARKDOWN)
            await message.forward(config.TECHSUPPORT_CHAT_ID)

    else:
        if str(message.chat.id) == config.TECHSUPPORT_CHAT_ID:
            if message.reply_to_message is not None and bot.id == message.reply_to_message.from_user.id:
                if message.reply_to_message.forward_from is not None:
                    if str(message.reply_to_message.forward_from.id) != config.BOT_TOKEN.split(':')[0]:
                        await send_message(message.reply_to_message.forward_from.id, message.text)
                else:
                    search = re.search(r'tg://user\?id=(?P<uid>\d+)', message.reply_to_message.md_text)
                    if search:
                        await send_message(int(search.group('uid')), message.text)


async def query_handler(query: types.CallbackQuery):
    user = await users.find_one({'uid': query.from_user.id})
    if user is None:
        await query.answer()
        return

    if query.data.startswith('SetLang'):
        lang = query.data.split('SetLang', 1)[1]
        await users.find_one_and_update({'uid': query.from_user.id}, {'$set': {'lang': lang}})
        await query.message.edit_text(t('CHOOSE_ACTION', locale=lang), reply_markup=keyboards.get_user_keyboard(lang))
    elif query.data.startswith('SetInitLang'):
        lang = query.data.split('SetInitLang', 1)[1]
        await users.find_one_and_update({'uid': query.from_user.id}, {'$set': {'lang': lang}})
        await query.message.edit_text(t('HELLO', locale=lang), parse_mode=types.ParseMode.MARKDOWN)
    elif query.data.startswith('Lang'):
        await query.message.edit_text('Выберите язык\nОберіть мову', reply_markup=keyboards.get_lang_keyboard())
    elif query.data.startswith('Sex'):
        sex = query.data.split('Sex', 1)[1]
        await users.find_one_and_update({'uid': query.from_user.id}, {'$set': {'sex': sex}, '$inc': {'p_stage': 1}})
        await query.message.delete_reply_markup()
        await send_message(query.from_user.id, t('CHOOSE_DATE', locale=user['lang']))
    elif query.data.startswith('City'):
        city = int(query.data.split('City', 1)[1])
        await users.find_one_and_update({'uid': query.from_user.id}, {'$set': {'city': city}})
        await query.message.edit_text(t('CHOOSE_CITY', locale=user['lang']),
                                      reply_markup=keyboards.get_subplaces_keyboard(city))
    elif query.data.startswith('SubCity'):
        subcity = int(query.data.split('SubCity', 1)[1])
        await users.find_one_and_update({'uid': query.from_user.id}, {'$set': {'subcity': subcity},
                                                                      '$inc': {'p_stage': 1}})
        await query.message.delete()
        await send_message(query.from_user.id, t('CHOOSE_VACS', locale=user['lang']),
                           parse_mode=types.ParseMode.MARKDOWN)

    elif query.data.startswith('TechSupport'):
        await users.find_one_and_update({'uid': query.from_user.id}, {'$set': {'stage': Stages.tech_support}})
        await send_message(query.from_user.id, t('TECHSUPPORT', locale=user['lang']),
                           parse_mode=types.ParseMode.MARKDOWN, reply_markup=keyboards.get_menu_keyboard(user['lang']))
        await query.message.delete_reply_markup()

    elif query.data.startswith('Menu'):
        await users.find_one_and_update({'uid': query.from_user.id}, {'$set': {'stage': Stages.info}})
        await query.message.edit_text(t('CHOOSE_ACTION', locale=user['lang']),
                                      reply_markup=keyboards.get_user_keyboard(user['lang']) if user[
                                                                                                    'uid'] not in config.ADMINS else
                                      keyboards.get_admuser_keyboard(user['lang']))

    elif query.data.startswith('Profile'):
        await query.message.edit_text(t('PROFILE', locale=user['lang'], name=user["name"], date=user["date"],
                                        month=user["month"], decade=user["decade"], year=user["year"],
                                        city=config.CHANNELS[user["city"]][0] if user["subcity"] == -1 else
                                        config.CHANNELS[user["city"]][2][user["subcity"]],
                                        vacs=", ".join(user["checks"])),
                                      reply_markup=keyboards.get_edit_keyboard(user['lang']),
                                      parse_mode=types.ParseMode.HTML)

    elif query.data.startswith('ChangeName'):
        await users.find_one_and_update({'uid': query.from_user.id}, {'$set': {'stage': Stages.edit,
                                                                               'p_stage': PStages.name}})
        await query.message.edit_text(t('CHOOSE_NAME', locale=user['lang']))
    elif query.data.startswith('ChangeBirthday'):
        await users.find_one_and_update({'uid': query.from_user.id}, {'$set': {'stage': Stages.edit,
                                                                               'p_stage': PStages.birthday}})
        await query.message.edit_text(t('CHOOSE_DATE', locale=user['lang']))

    elif query.data.startswith('ChangeCityVac'):
        await users.find_one_and_update({'uid': query.from_user.id}, {'$set': {'p_stage': PStages.city,
                                                                               'stage': Stages.edit}})
        await query.message.edit_text(t('CHOOSE_CITY', locale=user['lang']),
                                      reply_markup=keyboards.get_places_keyboard())

    elif query.data.startswith('BroadcastAccept'):
        from_user = user
        send_num = 0
        async for user in users.find({"stage": 1, "p_stage": 5}):
            try:
                if 'b_doc' in from_user:
                    await bot.send_document(user['uid'], from_user['b_doc'])
                elif 'b_photo' in from_user:
                    await bot.send_photo(user['uid'], from_user['b_photo'])
                elif 'b_text' in from_user:
                    await bot.send_message(user['uid'], from_user['b_text'], parse_mode=types.ParseMode.HTML)
                else:
                    await bot.forward_message(user['uid'], query.from_user.id, from_user['broadcast_msg'])
                await asyncio.sleep(0.05)
                send_num += 1
            except Exception as e:
                logger.warning(f'Failed to resend message to {user["uid"]}: {e}')
        await users.find_one_and_update({'uid': query.from_user.id}, {'$set': {'stage': Stages.info},
                                                                      '$unset': {'broadcast_msg': '',
                                                                                 'b_doc': '',
                                                                                 'b_photo': '',
                                                                                 'b_text': ''}})
        await query.message.edit_text(text=f'Разослано {send_num} пользователям. Выберите действие:',
                                      reply_markup=keyboards.get_user_keyboard(user['lang']) if user[
                                                                                                    'uid'] not in config.ADMINS else
                                      keyboards.get_admuser_keyboard(user['lang']))
    elif query.data.startswith('BroadcastCancel'):
        await users.find_one_and_update({'uid': query.from_user.id}, {'$set': {'stage': Stages.info},
                                                                      '$unset': {'broadcast_msg': '',
                                                                                 'b_doc': '',
                                                                                 'b_photo': '',
                                                                                 'b_text': ''}})
        await query.message.edit_text(text=t('CHOOSE_ACTION', locale=user['lang']),
                                      reply_markup=keyboards.get_user_keyboard(user['lang']) if user[
                                                                                                    'uid'] not in config.ADMINS else
                                      keyboards.get_admuser_keyboard(user['lang']))
    elif query.data.startswith('BCreate') and query.from_user.id in config.ADMINS:
        await send_message(query.from_user.id, 'Отправьте сообщение/фотографию/документ/опрос для рассылки')
        await users.find_one_and_update({'uid': query.from_user.id}, {'$set': {'stage': Stages.broadcast}})
    elif query.data.startswith('Dump'):
        await get_dump(query.message)
        await query.answer()
    else:
        logger.warning(f"Unknown query: {query.data}")


async def send_welcome_handler(message: types.Message):
    user = await users.find_one({"uid": message.from_user.id, "checks": {"$exists": True}})
    if user is None:
        await users.replace_one({'uid': message.from_user.id}, {'uid': message.from_user.id, 'stage': Stages.user_data,
                                                                'p_stage': PStages.name,
                                                                'full_name': message.from_user.full_name, 'checks': []},
                                upsert=True)

        await send_message(message.from_user.id, 'Выберите язык\nОберіть мову',
                           reply_markup=keyboards.get_init_lang_keyboard())
    else:
        await send_message(message.from_user.id, text=t('CHOOSE_ACTION', locale=user['lang']),
                           reply_markup=keyboards.get_user_keyboard(
                               user['lang']) if message.from_user.id not in config.ADMINS else
                           keyboards.get_admuser_keyboard(user['lang']))


async def get_dump(message: types.Message):
    wb = Workbook()
    ws = wb.active
    ws.append(("Имя", "Телефон", "Д.р.", "Пол", "Город", "Область", "Фильтры"))
    async for user in users.find({"stage": 1, "p_stage": 5}):
        ws.append((user['name'], user['phone'], f"{user['date']}.{user['month']}.{user['decade']}{user['year']}",
                   user['sex'], config.CHANNELS[user['city']][0], config.CHANNELS[user['city'][2][user['subcity']]]
                   if user['subcity'] != -1 else config.CHANNELS[user['city']][0], str(user['checks'])))
    wb_file = BytesIO(save_virtual_workbook(wb))
    wb_file.name = 'db.xlsx'
    await message.reply_document(wb_file)


async def broadcast_cmd_handler(message: types.Message):
    if not await users.find_one({"uid": message.from_user.id, "checks": {"$exists": True}}):
        await send_message(message.from_user.id, 'Для рассылки необходимо пройти регистрацию в боте')
    else:
        await send_message(message.from_user.id, 'Отправьте сообщение/фотографию/опрос для рассылки')
        await users.find_one_and_update({'uid': message.from_user.id}, {'$set': {'stage': Stages.broadcast}})


async def broadcast_handler(message: types.Message):
    user = await users.find_one({"uid": message.from_user.id, "stage": Stages.broadcast})
    if user is None:
        return
    await users.find_one_and_update({'uid': message.from_user.id}, {'$unset': {'broadcast_msg': '',
                                                                               'b_doc': '',
                                                                               'b_photo': '',
                                                                               'b_text': ''}})
    if message.content_type == types.ContentType.PHOTO:
        await users.find_one_and_update({"uid": user["uid"]}, {"$set": {"b_photo": message.photo[0].file_id}})
    elif message.content_type == types.ContentType.DOCUMENT:
        await users.find_one_and_update({"uid": user["uid"]}, {"$set": {"b_doc": message.document.file_id}})
    elif message.content_type == types.ContentType.TEXT:
        await users.find_one_and_update({"uid": user["uid"]}, {"$set": {"b_text": message.html_text}})
    else:
        await users.find_one_and_update({"uid": user["uid"]}, {"$set": {"broadcast_msg": message.message_id}})
    await message.reply("Разослать это сообщение?\nМожно отправить исправленное сообщение.",
                        reply_markup=keyboards.get_broadcast_keyboard(user['lang']))


def apply_handlers(dp):
    handlers = [
        {'fun': send_welcome_handler, 'named': {'commands': ['start', 'help']}},
        {'fun': get_dump, 'named': {'commands': ['dump'], 'user_id': config.ADMINS}},
        {'fun': broadcast_cmd_handler, 'named': {'commands': ['broadcast'], 'user_id': config.ADMINS}},
        # {'fun': test, 'named': {'commands': ['test']}},
        # {'fun': cleanup, 'named': {'commands': ['cleanup']}},
        {'fun': text_message_handler, 'named': {'content_types': types.ContentType.TEXT}},
        {'fun': broadcast_handler, 'named': {'content_types': types.ContentType.PHOTO}},
        {'fun': broadcast_handler, 'named': {'content_types': types.ContentType.POLL}},
        {'fun': broadcast_handler, 'named': {'content_types': types.ContentType.VIDEO}},
        {'fun': broadcast_handler, 'named': {'content_types': types.ContentType.VIDEO_NOTE}},
        {'fun': broadcast_handler, 'named': {'content_types': types.ContentType.DOCUMENT}},

        # {'fun': photo_message_handler, 'named': {'content_types': types.ContentType.PHOTO}},
        # {'fun': document_message_handler, 'named': {'content_types': types.ContentType.DOCUMENT}},
    ]

    for handler in handlers:
        dp.register_message_handler(handler['fun'], **handler['named'])
        dp.register_callback_query_handler(query_handler)
