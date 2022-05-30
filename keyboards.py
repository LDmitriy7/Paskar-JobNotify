from aiogram import types
from i18n import t

from config import CHANNELS


def divide_chunks(a, n):
    for i in range(0, len(a), n):
        yield a[i:i + n]


def get_places_keyboard(_lang='ru'):
    keyboard_items = []
    for num, channel in enumerate(CHANNELS):
        keyboard_items.append(types.InlineKeyboardButton(text=channel[0], callback_data=f'City{num}'))

    return types.InlineKeyboardMarkup(
        row_width=2,
        inline_keyboard=list(divide_chunks(keyboard_items, 2))
    )


def get_subplaces_keyboard(num, _lang='ru'):
    keyboard_items = [types.InlineKeyboardButton(text=CHANNELS[num][0], callback_data=f'SubCity-1')]
    for num, subcity in enumerate(CHANNELS[num][2]):
        keyboard_items.append(types.InlineKeyboardButton(text=subcity, callback_data=f'SubCity{num}'))

    return types.InlineKeyboardMarkup(
        row_width=2,
        inline_keyboard=list(divide_chunks(keyboard_items, 2))
    )


def get_sex_keyboard(lang):
    return types.InlineKeyboardMarkup(
        row_width=2,
        inline_keyboard=[[types.InlineKeyboardButton(text=t('MALE_BTN', locale=lang), callback_data=f'SexМ')],
                         [types.InlineKeyboardButton(text=t('FEMALE_BTN', locale=lang), callback_data=f'SexЖ')]]
    )


# def get_vacs_keyboard(marked, lang):
#     keyboard_items = []
#     for num, value in enumerate(VACS):
#         if num in marked:
#             keyboard_items.append(types.InlineKeyboardButton(text=f'{value}✅', callback_data=f'Uncheck{num}'))
#         else:
#             keyboard_items.append(types.InlineKeyboardButton(text=f'{value}', callback_data=f'Check{num}'))
#     keyboard_items = list(divide_chunks(keyboard_items, 2))
#     keyboard_items.append([types.InlineKeyboardButton(text=f'Отправить', callback_data=f'Done')])
#     return types.InlineKeyboardMarkup(
#         row_width=2,
#         inline_keyboard=keyboard_items
#     )


def get_user_keyboard(lang):
    return types.InlineKeyboardMarkup(
        row_width=2,
        inline_keyboard=(
            (
                types.InlineKeyboardButton(text=t('PROFILE_BTN', locale=lang), callback_data='Profile'),
                # types.InlineKeyboardButton(text='Про бота', url='https://horeca-job.com.ua/')
            ),
            (
                types.InlineKeyboardButton(text=t('TECHSUPPORT_BTN', locale=lang), callback_data='TechSupport'),
                types.InlineKeyboardButton(text=t('OURSITE_BTN', locale=lang), url='https://horeca-job.com.ua/')
            ),
            (
                types.InlineKeyboardButton(text='Язык/Мова', callback_data='Lang'),
            )
        )
    )


def get_admuser_keyboard(lang):
    return types.InlineKeyboardMarkup(
        row_width=2,
        inline_keyboard=(
            (
                types.InlineKeyboardButton(text=t('PROFILE_BTN', locale=lang), callback_data='Profile'),
                # types.InlineKeyboardButton(text='Про бота', url='https://horeca-job.com.ua/')
            ),
            (
                types.InlineKeyboardButton(text=t('TECHSUPPORT_BTN', locale=lang), callback_data='TechSupport'),
                types.InlineKeyboardButton(text=t('OURSITE_BTN', locale=lang), url='https://horeca-job.com.ua/')
            ),
            (
                types.InlineKeyboardButton(text='Рассылка', callback_data='BCreate'),
                types.InlineKeyboardButton(text='Дамп', callback_data='Dump')
            ),
            (
                types.InlineKeyboardButton(text='Язык/Мова', callback_data='Lang'),
            )
        )
    )


def get_menu_keyboard(lang):
    return types.InlineKeyboardMarkup(
        row_width=3,
        inline_keyboard=(
            (
                types.InlineKeyboardButton(text=t('MENU_BTN', locale=lang), callback_data=f'Menu'),
            ),
        )
    )


def get_broadcast_keyboard(_lang):
    return types.InlineKeyboardMarkup(
        row_width=3,
        inline_keyboard=(
            (
                types.InlineKeyboardButton(text='Разослать', callback_data=f'BroadcastAccept'),
            ), (
                types.InlineKeyboardButton(text='Отмена', callback_data=f'BroadcastCancel'),
            ),
        )
    )


def get_lang_keyboard():
    return types.InlineKeyboardMarkup(
        row_width=2,
        inline_keyboard=(
            (
                types.InlineKeyboardButton(text='🇷🇺 Русский', callback_data='SetLangru'),
            ),
            (
                types.InlineKeyboardButton(text='🇺🇦 Українська', callback_data='SetLangua'),
            ),
        )
    )


def get_init_lang_keyboard():
    return types.InlineKeyboardMarkup(
        row_width=2,
        inline_keyboard=(
            (
                types.InlineKeyboardButton(text='🇷🇺 Русский', callback_data='SetInitLangru'),
            ),
            (
                types.InlineKeyboardButton(text='🇺🇦 Українська', callback_data='SetInitLangua'),
            ),
        )
    )


def get_edit_keyboard(lang):
    return types.InlineKeyboardMarkup(
        row_width=2,
        inline_keyboard=(
            (
                types.InlineKeyboardButton(text=t('NAME_BTN', locale=lang), callback_data=f'ChangeName'),
                types.InlineKeyboardButton(text=t('BIRTHDAY_BTN', locale=lang), callback_data=f'ChangeBirthday'),
            ),
            (
                types.InlineKeyboardButton(text=t('VACS_BTN', locale=lang), callback_data=f'ChangeCityVac'),
            ),
            (
                types.InlineKeyboardButton(text=t('MENU_BTN', locale=lang), callback_data=f'Menu'),
            ),
        )
    )
