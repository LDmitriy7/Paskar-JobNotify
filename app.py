import asyncio
import logging
from os import getcwd, path

import i18n
import motor.motor_asyncio
from aiogram import Bot, Dispatcher, exceptions
from telethon.sync import TelegramClient, events

import commands
import config
from config import API_HASH, API_ID, DB_HOST


def levenshtein_distance(first, second):
    """Find the Levenshtein distance between two strings."""
    if len(first) > len(second):
        first, second = second, first
    if len(second) == 0:
        return len(first)
    first_length = len(first) + 1
    second_length = len(second) + 1
    distance_matrix = [[0] * second_length for _ in range(first_length)]
    for i in range(first_length):
        distance_matrix[i][0] = i
    for j in range(second_length):
        distance_matrix[0][j] = j
    for i in range(1, first_length):
        for j in range(1, second_length):
            deletion = distance_matrix[i - 1][j] + 1
            insertion = distance_matrix[i][j - 1] + 1
            substitution = distance_matrix[i - 1][j - 1]
            if first[i - 1] != second[j - 1]:
                substitution += 1
            distance_matrix[i][j] = min(insertion, deletion, substitution)
    return distance_matrix[first_length - 1][second_length - 1]


def percent_diff(first, second):
    return 100 * levenshtein_distance(first, second) / float(max(len(first), len(second)))


# Database setup
db_client = motor.motor_asyncio.AsyncIOMotorClient(host=DB_HOST)
db = db_client.job_notify_bot

# {uid: 123456789, stage: int, p_stage: int,
# date: str, month: str, decade: str, year: str, name: str, full_name: str, sex: str, city: int, subcity: int,
# checks=[]}

users = db.users

# Logging setup
logging.basicConfig(level=logging.INFO, filename='.log', filemode='w')
logger = logging.getLogger('bot')
logger.setLevel(logging.DEBUG)
lh = logging.StreamHandler()
lh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
for h in logger.handlers:
    logger.removeHandler(h)
logger.addHandler(lh)

# i18n setup

cwd = getcwd()
translations_dir = path.abspath(path.join(cwd, 'translations'))
if not path.isdir(translations_dir):
    logger.error(f"i18n: Translations path ({translations_dir}) does not exist")
    exit(-1)

i18n.load_path.append(translations_dir)
i18n.set('filename_format', '{locale}.{format}')
i18n.set('locale', 'ru')
i18n.set('fallback', 'ru')

# Bot setup
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot)


class Index:
    value = -1


# async def test(message: types.Message):
#     channel_username = 'tehrandb'  # your channel
#     channel_entity = await client.get_input_entity('https://t.me/joinchat/AAAAAFNd1ZM9vVilU6TaIQ')
#     messages = await client(GetHistoryRequest(
#         peer=channel_entity,
#         limit=100,
#         offset_date=None,
#         offset_id=0,
#         max_id=0,
#         min_id=0,
#         add_offset=0,
#         hash=0
#     ))
#     for message in messages.messages:
#         text = message.message.splitlines()
#         if len(text) < 6:
#             return  # suitable message not found
#
#         city_index = Index()
#         city = list(filter(lambda x: x[1] == '-100' + str(1398658451)
#                                      and (setattr(city_index, 'value', config.CHANNELS.index(x)) is None),
#                            config.CHANNELS))[0]
#
#         # print('City index:', city_index.value)
#         addr = text[1].replace('*', '').replace('`', '').strip().lower()
#         subcity_index = Index()
#         any(map(lambda x: addr.startswith(x.lower()) and (setattr(subcity_index, 'value', city[2].index(x))), city[2]))
#         # print('Subcity index:', subcity_index.value)
#         vac_strings = list(filter(lambda x: '•' in x, text))
#         sent_to = []
#         for vac in vac_strings:
#             vac = vac.replace('•', '').replace('*', '').lower().strip()
#             async for user in users.find({'city': city_index.value, 'subcity': subcity_index.value}):
#                 if any(map(lambda x: True if (100 - percent_diff(x, vac)) >= 60 else False, user['checks'])):
#                     try:
#                         if user['uid'] not in sent_to:
#                             await bot.forward_message(user['uid'], '-100' + str(1398658451), message.id)
#                             sent_to.append(user['uid'])
#                     except exceptions.BotBlocked:
#                         await users.delete_one({'uid': user['uid']})
#                         logger.info('Removed', user['uid'], '(blocked bot)')
#                     except Exception as e:
#                         logger.error(str(e) + 'shit')  # shit happened


if __name__ == "__main__":
    client = TelegramClient('mycloud', API_ID, API_HASH).start()


    @client.on(events.NewMessage(chats=config.CHATS))
    async def handler(event: events.NewMessage.Event):
        chat = await event.get_chat()
        text = event.message.text.splitlines()
        if len(text) < 6:
            return  # suitable message not found

        city_index = Index()
        city = list(filter(lambda x: x[1] == '-100' + str(chat.id) and (
                setattr(city_index, 'value', config.CHANNELS.index(x)) is None),
                           config.CHANNELS))[0]

        # print('City index:', city_index.value)
        addr = text[1].replace('*', '').replace('`', '').strip().lower()
        subcity_index = Index()
        any(map(lambda x: addr.startswith(x.lower()) and (setattr(subcity_index, 'value', city[2].index(x))), city[2]))
        # print('Subcity index:', subcity_index.value)
        vac_strings = list(filter(lambda x: '•' in x, text))
        sent_to = []
        for vac in vac_strings:
            vac = vac.replace('•', '').replace('*', '').lower().strip()
            async for user in users.find({'city': city_index.value, 'subcity': subcity_index.value}):
                if any(map(lambda x: True if (100 - percent_diff(x, vac)) >= 60 else False, user['checks'])):
                    try:
                        if user['uid'] not in sent_to:
                            await bot.forward_message(user['uid'], '-100' + str(chat.id), event.message.id)
                            sent_to.append(user['uid'])
                    except exceptions.BotBlocked:
                        await users.delete_one({'uid': user['uid']})
                        logger.info('Removed', user['uid'], '(blocked bot)')
                    except Exception as e:
                        logger.error(e)  # bad things happened


    loop = asyncio.get_event_loop()
    # dp.register_message_handler(test, commands=['test'])
    commands.apply_handlers(dp)
    loop.run_until_complete(dp.skip_updates())
    loop.create_task(dp.start_polling())

    with client:
        client.run_until_disconnected()
