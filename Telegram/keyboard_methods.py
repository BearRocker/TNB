from DataBases.select_methods import select_user_tournaments, select_tournaments_by_id
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def choose_discipline():  # Keyboard markup maker for disciplines
    key_apex = InlineKeyboardButton(text="Apex", callback_data="Apex")
    key_cs = InlineKeyboardButton(text="CS", callback_data="CS2")
    key_dota = InlineKeyboardButton(text="Dota 2", callback_data="DOTA2")
    key_subs = InlineKeyboardButton(text="Выбранные турниры", callback_data="Subs")
    keyboard = [[key_apex],[key_cs],[key_dota],[key_subs]]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return markup


async def subscriptions():  # keyboard markup maker for subs menu
    keyboard = [[InlineKeyboardButton(text="Назад", callback_data='Back disciplines')]]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return markup

async def start_sub_check():
    keys = [[InlineKeyboardButton(text='ТГ канал', url="https://t.me/+n-81CI4xTelhZjgy")],
            [InlineKeyboardButton(text="Проверить подписку", callback_data="Проверить подписку")]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=keys)
    return keyboard



async def start_menu():  # Main menu from which you can select (no return to this menu 13.09)
    key_subs = InlineKeyboardButton(text="Выбранные турниры", callback_data="Subs")
    key_disciplines = InlineKeyboardButton(text="Выбрать дисциплину", callback_data="Choose discipline")
    keyboard = [[key_disciplines], [key_subs]]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return markup


async def search_for_tier(discipline,tiers):  # Keyboard markup maker for choosing tiers
    keyboard = [[InlineKeyboardButton(text="S", callback_data=f"{discipline}|{tiers[0]}")],
                [InlineKeyboardButton(text="A", callback_data=f"{discipline}|{tiers[1]}")],
                [InlineKeyboardButton(text="B", callback_data=f"{discipline}|{tiers[2]}")],
                [InlineKeyboardButton(text="Назад к выбору дисциплины", callback_data=f"Back")]]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return markup


async def for_tournaments(tournaments, tier, user_id, discipline):  # Keyboard markup for 10 tournaments of specific tier user choosed
    markup = InlineKeyboardBuilder()
    tournaments_prize = []
    user_tournaments = await select_user_tournaments(user_id)
    if user_tournaments[0] != '':
        user_tournaments = user_tournaments[0].split(',')
        for i in range(len(user_tournaments)):
            user_tournaments[i] = await select_tournaments_by_id(int(user_tournaments[i]))
            user_tournaments[i] = user_tournaments[i][0]
        for i in tournaments:
            if i["tier"] == tier:
                tournaments_prize.append((i['tournament'], i['prize']))
        tournaments_prize = sorted(tournaments_prize, key=lambda x: x[1] if x[1] == 0 else float(''.join(x[1][1:].split(','))) if x[1] != '\xa0' else 0)
        for t in tournaments_prize[:10]:
            if t[0] in user_tournaments:
                markup.button(text=t[0] + '✅', callback_data="t" + "+" + t[0])
            else:
                markup.button(text=t[0] + '❌', callback_data="t" + "+" + t[0])
        if len(markup.export()) == 0:
            markup.button(text="Сейчас турниров такого тира не ожидается", callback_data=f"Back tier|{discipline}")
        markup.button(text="Назад к выбору тира", callback_data=f"Back tier|{discipline}")
        markup.adjust(1)
        return markup
    else:
        try:
            for i in tournaments:
                if i["tier"] == tier:
                    tournaments_prize.append((i['tournament'], i['prize']))
            tournaments_prize = sorted(tournaments_prize, key=lambda x: x[1] if x[1] == 0 else float(''.join(x[1][1:].split(','))) if x[1] != '\xa0' else 0)
            for t in tournaments_prize[:10]:
                if t[0] in user_tournaments:
                    markup.button(text=t[0] + '✅', callback_data="t" + "+" + t[0])
                else:
                    markup.button(text=t[0] + '❌', callback_data="t" + "+" + t[0])
            if len(markup.export()) == 0:
                markup.button(text="Сейчас турниров такого тира не ожидается", callback_data=f"Back tier|{discipline}")
            markup.button(text="Назад к выбору тира", callback_data=f"Back tier|{discipline}")
            markup.adjust(1)
            return markup
        except Exception as e:
            logger.exception(msg=e)


async def delete_notification(tournament):  # Menu for deleting or not tournament from subs
    keyboard = [[InlineKeyboardButton(text="Да", callback_data="Delete" + "+" + tournament)],
                [InlineKeyboardButton(text="Нет", callback_data="Mistake")]]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return markup