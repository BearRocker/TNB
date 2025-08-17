import aiogram.exceptions
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.loggers import dispatcher

from DataBases.add_methods import add_user
from DataBases.update_methods import update_user_tournaments
from Disciplines.Apex import Apex
from Disciplines.CS2 import CS
from Disciplines.Dota2 import DOTA2
from Disciplines.R6S import R6S
from Disciplines.Valorant import Valorant
import logging
import asyncio
from aiogram import BaseMiddleware
from typing import Any, Awaitable, Callable, Dict
from aiogram.types import TelegramObject
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart, Command
from DataBases.select_methods import select_user_by_id, select_user_tournaments, select_tournament_by_name, \
    select_users, select_game_by_id, select_all_tournaments
from DataBases import database_update
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dateutil import parser
from datetime import timedelta
import Config
from keyboard_methods import *

dispatcher = Dispatcher()


async def check(): # Проверка времени до начала матча и на проверку прошедших турниров в подписках
    # Checking time before start matches and for checking concluded tournaments in subs
    users = await select_users()
    all_tournaments = []
    for cs_t in cs_tournaments:
        all_tournaments.append([cs_t["tournament"], 2])
    for dota_t in dota_tournaments:
        all_tournaments.append([dota_t["tournament"], 3])
    for a_t in apex_tournaments:
        all_tournaments.append([a_t["tournament"], 1])
    for r_t in r6s_tournaments:
        all_tournaments.append([r_t["tournament"], 4])
    for v_t in valorant_tournaments:
        all_tournaments.append([v_t["tournament"], 5])
    tournaments_soon = await database_update.get_tournament_db()
    for i in range(len(all_tournaments)):
        a = await select_tournament_by_name_and_discipline(all_tournaments[i][0], all_tournaments[i][1])
        if len(a) != 0:
            all_tournaments[i] = int(a[0].to_dict()['TournamentID'])
    for user in users:
        tournaments = user.TournamentsID
        tournaments_deprived = tournaments.split(',')
        res = tournaments.split(',')
        for tournament in tournaments_deprived:
            if tournament != '':
                tournament_name = await select_tournaments_by_id(int(tournament))
                tournament_name = tournament_name[0].to_dict()["Name"]
                for tournament_soon in tournaments_soon:
                    if int(tournament) == int(tournament_soon.TournamentsID):
                        today = datetime.today()
                        if (today + timedelta(hours=int(user.Settings.split()[0]))).strftime('%y-%m-%d %H:%M') == parser.parse(
                                tournament_soon.Time).strftime('%y-%m-%d %H:%M'):
                            await bot.send_message(chat_id=user.ChatID,
                                                   text=f"Уведомление за 1 час да старта матчей на {tournament_name}")
                        elif today.strftime('%y-%m-%d %H:%M') == parser.parse(tournament_soon.Time).strftime(
                                '%y-%m-%d %H:%M'):
                            await bot.send_message(chat_id=user.ChatID,
                                                   text=f"Матчи на {tournament_name} НАЧАЛИСЬ")
                if int(tournament) not in all_tournaments:
                    res.remove(tournament)
                    await update_user_tournaments(user.ChatID, ','.join(res))


async def update_db():  # Обновление ДБ каждый день в 6 утра по Пермскому
    # Updating DB every day at 6:00 +2 MSK
    global apex_tournaments, cs_tournaments, dota_tournaments, disciplines, r6s_tournaments, valorant_tournaments
    # await bot.send_message(chat_id=Config.bot_channel_id, text='Бот ушёл на обновление баз данных будет доступен через 10 минут') уже не нужно, оставил на всякий
    apex_tournaments = await apex.get_tournament()
    cs_tournaments = await cs.get_tournament()
    dota_tournaments = await dota2.get_tournament()
    r6s_tournaments = await r6s.get_tournament()
    valorant_tournaments = await valorant.get_tournament()
    disciplines = {"Apex Legends": apex_tournaments, "CS2": cs_tournaments, "Dota2": dota_tournaments, "R6S": r6s_tournaments, "Valorant": valorant_tournaments}
    await database_update.update_db()


async def update_db_command():  # Делает тоже самое, что и команда выше, только её возможно вызвать через telegram
    global apex_tournaments, cs_tournaments, dota_tournaments, disciplines, r6s_tournaments, valorant_tournaments
    apex_tournaments = await apex.get_tournament()
    cs_tournaments = await cs.get_tournament()
    dota_tournaments = await dota2.get_tournament()
    r6s_tournaments = await r6s.get_tournament()
    valorant_tournaments = await valorant.get_tournament()
    disciplines = {"Apex Legends": apex_tournaments, "CS2": cs_tournaments, "Dota2": dota_tournaments, "R6S": r6s_tournaments, "Valorant": valorant_tournaments}
    await database_update.update_db()

# Starting up every minute check
# Проверка для уведомления пользователя
#aioschedule.every(30).seconds.do(check)
#aioschedule.every(1).seconds.do(update_db)


# "/start" message
# Сообщение при команде "/start"
@dispatcher.message(CommandStart())
async def start_message(message: Message):
    keyboard = await start_sub_check()
    await bot.send_message(chat_id=message.chat.id,text='Привет, это бот для уведомлений о начале матчей на киберспортивных турнирах. Для начала работы подпишись на телеграмм канал.',
                           reply_markup=keyboard)


# Checking is user subbed
# Проверяет подписан ли пользователь
async def is_sub(user_id : int) -> bool:
    try:
        res = await bot.get_chat_member(chat_id=Config.bot_channel_id, user_id=user_id)
        if res:
            return True
        else:
            raise aiogram.exceptions.TelegramAPIError
    except aiogram.exceptions.TelegramAPIError:
        logger.exception("Bad Request: user not found")
        return False


# Команда для ручного обновления матчей
@dispatcher.message(Command('b01cf5cb16d9d3e487d58ab8297dc5e6'))
async def upgrade_people_upgrade(message: Message):
    await message.answer('Let\'s go gambling...')
    await update_db_command()

# Обработка сообщения для просмотра дисциплин
@dispatcher.callback_query(F.data == "Choose discipline")
async def choose_discipline_callback(call: CallbackQuery):
    markup = await choose_discipline()
    await bot.edit_message_text(chat_id=call.message.chat.id, text="Выбирай дисциплину", reply_markup=markup, message_id=call.message.message_id)

# Проверка на подписку при нажатии на кнопку
@dispatcher.callback_query(F.data == "Проверить подписку")
async def check_subs(call: CallbackQuery):
    sub = await is_sub(call.from_user.id)
    if not sub:
        keyboard = await start_sub_check()
        await bot.edit_message_text("Вы не подписаны на канал, для работы бота подпишитесь на канал.",
                                    message_id=call.message.message_id, chat_id=call.message.chat.id,
                                    reply_markup=keyboard)
    else:
        markup = await start_menu()
        await bot.edit_message_text("Отлично ты подписан!", message_id=call.message.message_id,
                                    chat_id=call.message.chat.id)
        await bot.send_message(chat_id=call.message.chat.id, text="Главное меню", reply_markup=markup)
        user_exists = await select_user_by_id(call.message.chat.id)
        if len(user_exists) == 0:
            await add_user({'ChatID': call.message.chat.id, 'TournamentsID': '', "Settings": '1 hour'})

# Обработка кнопок нажатий на определённый тир турниров по Apex
@dispatcher.callback_query(F.data.startswith("Apex"))
async def Apex_tiers(call: CallbackQuery):
    tier = call.data.split('|')[1] if len(call.data.split('|'))>1 else None # Tier = S-Tier, A-Tier, B-Tier
    if tier:
        if "Back" not in tier:
            markup = await for_tournaments(apex_tournaments, tier, call.message.chat.id, "Apex Legends")
            await bot.edit_message_text(f"Вы выбрали тир {tier} турниров по Apex Legends", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup.as_markup())
    else:
        markup = await search_for_tier('Apex', ["S-Tier", "A-Tier", "B-Tier"])
        await bot.edit_message_text("Вы выбрали дисциплину Apex Legends", chat_id=call.message.chat.id,
                                    message_id=call.message.message_id, reply_markup=markup)

# Обработка кнопок нажатий на определённый тир турниров по Apex
@dispatcher.callback_query(F.data.contains('Back'))
async def back_to(call: CallbackQuery):
    discipline = call.data.split("|")[1] if len(call.data.split("|"))>1 else None
    menu = call.data.split()[1] if len(call.data.split()) > 1 else None
    tier = call.data.split("|")[2] if len(call.data.split("|")) > 2 else None
    if discipline == "Apex Legends":
        if tier:
            markup = await for_tournaments(apex_tournaments, tier, call.message.chat.id, "Apex")
            await bot.edit_message_text(f"Вы выбрали тир {tier} турниров по Apex Legends", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup.as_markup())
        else:
            markup = await search_for_tier('Apex', ["S-Tier", "A-Tier", "B-Tier"])
            await bot.edit_message_text("Вы выбрали дисциплину Apex Legends", chat_id=call.message.chat.id,
                                        message_id=call.message.message_id, reply_markup=markup)
    elif discipline == "CS2":
        if tier:
            markup = await for_tournaments(cs_tournaments, tier, call.message.chat.id, "CS2")
            await bot.edit_message_text(f"Вы выбрали тир {tier} турниров по CS2", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup.as_markup())
        else:
            markup = await search_for_tier('CS2', ["S-Tier", "A-Tier", "B-Tier"])
            await bot.edit_message_text("Вы выбрали дисциплину CS2", chat_id=call.message.chat.id,
                                        message_id=call.message.message_id, reply_markup=markup)
    elif discipline == "DOTA2":
        if tier:
            markup = await for_tournaments(dota_tournaments, tier, call.message.chat.id, "DOTA2")
            await bot.edit_message_text(f"Вы выбрали тир {tier} турниров по DOTA 2", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup.as_markup())
        else:
            markup = await search_for_tier('DOTA2', ["Tier 1", "Tier 2", "Tier 3"])
            await bot.edit_message_text("Вы выбрали дисциплину Dota 2", chat_id=call.message.chat.id,
                                        message_id=call.message.message_id, reply_markup=markup)
    elif discipline == "R6S":
        if tier:
            markup = await for_tournaments(r6s_tournaments, tier, call.message.chat.id, "R6S")
            await bot.edit_message_text(f"Вы выбрали тир {tier} турниров по R6S", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup.as_markup())
        else:
            markup = await search_for_tier('R6S', ["S-Tier", "A-Tier", "B-Tier"])
            await bot.edit_message_text("Вы выбрали дисциплину R6S", chat_id=call.message.chat.id,
                                        message_id=call.message.message_id, reply_markup=markup)
    elif discipline == "Valorant":
        if tier:
            markup = await for_tournaments(valorant_tournaments, tier, call.message.chat.id, "Valorant")
            await bot.edit_message_text(f"Вы выбрали тир {tier} турниров по Valorant", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup.as_markup())
        else:
            markup = await search_for_tier('Valorant', ["S-Tier", "A-Tier", "B-Tier"])
            await bot.edit_message_text("Вы выбрали дисциплину Valorant", chat_id=call.message.chat.id,
                                        message_id=call.message.message_id, reply_markup=markup)
    elif menu == "main":
        markup = await start_menu()
        await bot.edit_message_text("Главное меню", chat_id = call.message.chat.id, message_id=call.message.message_id,
                                    reply_markup=markup)
    else:
        markup = await choose_discipline()
        await bot.edit_message_text("Выбирай дисциплину", chat_id=call.message.chat.id,
                                    message_id=call.message.message_id, reply_markup=markup)


# Обработка кнопок нажатий на определённый тир турниров по CS2
@dispatcher.callback_query(F.data.startswith("CS2"))
async def CS2_tiers(call: CallbackQuery):
    tier = call.data.split('|')[1] if len(call.data.split('|')) > 1 else None  # Tier = S-Tier, A-Tier, B-Tier
    if tier:
        if "Back" not in tier:
            markup = await for_tournaments(cs_tournaments, tier, call.message.chat.id, "CS2")
            await bot.edit_message_text(f"Вы выбрали тир {tier} турниров по CS2", chat_id=call.message.chat.id,
                                        message_id=call.message.message_id, reply_markup=markup.as_markup())
    else:
        markup = await search_for_tier('CS2', ["S-Tier", "A-Tier", "B-Tier"])
        await bot.edit_message_text("Вы выбрали дисциплину CS2", chat_id=call.message.chat.id,
                                    message_id=call.message.message_id, reply_markup=markup)


# Обработка кнопок нажатий на определённый тир турниров по Dota 2
@dispatcher.callback_query(F.data.startswith("DOTA2"))
async def DOTA_tiers(call: CallbackQuery):
    tier = call.data.split('|')[1] if len(call.data.split('|')) > 1 else None  # Tier = Tier 1, Tier 2, Tier 3
    tier_to_normal = {"Tier 1":"S-Tier", "Tier 2":"A-Tier", "Tier 3":"B-Tier"}
    if tier:
        if "Back" not in tier:
            markup = await for_tournaments(dota_tournaments, tier, call.message.chat.id, "DOTA2")
            await bot.edit_message_text(f"Вы выбрали тир {tier_to_normal[tier]} турниров по Dota 2", chat_id=call.message.chat.id,
                                        message_id=call.message.message_id, reply_markup=markup.as_markup())
    else:
        markup = await search_for_tier('DOTA2', ["Tier 1", "Tier 2", "Tier 3"])
        await bot.edit_message_text("Вы выбрали дисциплину Dota 2", chat_id=call.message.chat.id,
                                    message_id=call.message.message_id, reply_markup=markup)


# Обработка кнопок нажатий на определённый тир турниров по R6s
@dispatcher.callback_query(F.data.startswith("R6S"))
async def r6s_tiers(call: CallbackQuery):
    tier = call.data.split('|')[1] if len(call.data.split('|'))>1 else None # Tier = S-Tier, A-Tier, B-Tier
    if tier:
        if "Back" not in tier:
            markup = await for_tournaments(r6s_tournaments, tier, call.message.chat.id, 'R6S')
            await bot.edit_message_text(f"Вы выбрали тир {tier} турниров по Rainbow 6 Siege", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup.as_markup())
    else:
        markup = await search_for_tier('R6S', ["S-Tier", "A-Tier", "B-Tier"])
        await bot.edit_message_text("Вы выбрали дисциплину Rainbow 6 Siege", chat_id=call.message.chat.id,
                                    message_id=call.message.message_id, reply_markup=markup)

# Обработка кнопок нажатий на определённый тир турниров по Valorant
@dispatcher.callback_query(F.data.startswith("Valorant"))
async def valorant_tiers(call: CallbackQuery):
    tier = call.data.split('|')[1] if len(call.data.split('|'))>1 else None # Tier = S-Tier, A-Tier, B-Tier
    if tier:
        if "Back" not in tier:
            markup = await for_tournaments(valorant_tournaments, tier, call.message.chat.id, 'Valorant')
            await bot.edit_message_text(f"Вы выбрали тир {tier} турниров по Valorant", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup.as_markup())
    else:
        markup = await search_for_tier('Valorant', ["S-Tier", "A-Tier", "B-Tier"])
        await bot.edit_message_text("Вы выбрали дисциплину Valorant", chat_id=call.message.chat.id,
                                    message_id=call.message.message_id, reply_markup=markup)

# Обработка кнопок нажатий для показывания текущих подписок
@dispatcher.callback_query(F.data.contains("Subs"))
@dispatcher.callback_query(F.data.startswith(">"))
@dispatcher.callback_query(F.data.startswith("<"))
async def show_subs(call: CallbackQuery):
    page = int(call.data.split("+")[1]) if len(call.data.split("+")) > 1 else 0
    user_tournaments_ids = await select_user_tournaments(call.message.chat.id)
    if user_tournaments_ids[0].split(',')[0] not in ['', ' ', "", " "]:
        user_tournaments_ids = list(map(int, user_tournaments_ids[0].split(','))) if len(user_tournaments_ids[0].split(",")) > 1 else [int(user_tournaments_ids[0])]
    else:
        user_tournaments_ids = list(map(int, user_tournaments_ids[0].split(',')))[1:] if len(
            user_tournaments_ids[0].split(",")) > 1 else []
    user_tournaments = []
    for i in user_tournaments_ids:
        tournament = await select_tournaments_by_id(i)
        user_tournaments.append([tournament[0].to_dict()["Name"], tournament[0].to_dict()["GameID"]])
    subs_keyboard = await subscriptions(user_tournaments, page)
    await bot.edit_message_text(f"Ваши выбранные подписки", chat_id=call.message.chat.id,
                          message_id=call.message.message_id, reply_markup=subs_keyboard.as_markup())

# Обработка для выведения информации о турнире с предложением подписаться на этот турнир
@dispatcher.callback_query(F.data.startswith('t+'))
async def add_tournament_to_db(call: CallbackQuery):
    global disciplines
    tournament = call.data.split("+")[1]
    disc_id = call.data.split("+")[-1]
    tournament = await select_tournament_by_name_and_discipline(tournament, int(disc_id))
    tournament_name = tournament[0].to_dict()["Name"]
    tournament_id = str(tournament[0].to_dict()["TournamentID"])
    tournament_discipline = await select_game_by_id(int(disc_id))
    tournament_discipline = str(tournament_discipline[0].Name)
    tournament_tier = tournament[0].to_dict()["Tier"]
    tournament_teams = tournament[0].to_dict()["TeamsCount"] if tournament[0].to_dict()["TeamsCount"] != "idk" else "Ещё не известно"
    tournament_prize = tournament[0].to_dict()["Prize"] if tournament[0].to_dict()["Prize"] != "0" else "Его нет"
    tournaments_selected = await select_user_tournaments(call.message.chat.id)
    tournament_date = tournament[0].to_dict()["Date"]
    tournament_location = tournament[0].to_dict()["Location"]
    discipline_id = tournament[0].to_dict()["GameID"]
    if tournament_id not in tournaments_selected[0]:
        markup = await show_tournament_info(tournament_discipline, tournament_tier, tournament_id)
        await bot.edit_message_text(f"Турнир: {tournament_name}\nКол-во команд: {tournament_teams}\nПризовой: {tournament_prize}\nТир турнира: {tournament_tier}\nДата проведения: {tournament_date}\nМесто проведения: {tournament_location}",
            message_id=call.message.message_id, reply_markup=markup, chat_id=call.message.chat.id)
    else:
        markup = await delete_notification(
            tournament_name + "+" + call.data.split("+")[-3] + "+s" if call.data.split("+")[-2] == "s" else tournament_name, discipline_id)
        await bot.edit_message_text(
            f"Вы хотите удалить турнир {tournament_tier} тира по {tournament_discipline} - {tournament_name} из своих оповещений?",
            chat_id=call.message.chat.id, message_id=call.message.message_id,
            reply_markup=markup)

# Обработка при нажатии кнопки "Подписаться"
@dispatcher.callback_query(F.data.startswith("Yes"))
async def sub(call: CallbackQuery):
    tournament_discipline, tournament_id = call.data.split("|")[1:]
    tournament = await select_tournaments_by_id(int(tournament_id))
    tournament_name = tournament[0].to_dict()["Name"]
    tournament_tier = tournament[0].to_dict()["Tier"]
    tournaments_selected = await select_user_tournaments(call.message.chat.id)
    discipline_id = tournament[0].to_dict()["GameID"]
    if len(tournaments_selected[0].split(',')) >= 1 and tournaments_selected[0].split(',')[0] not in ['', ' ', "", " "]:
        if tournament_id not in tournaments_selected[0].split(','):
            await update_user_tournaments(call.message.chat.id, tournaments_selected[0] + "," + tournament_id)
            discipline_dict = {"Apex Legends": "Apex Legends", "CS2": "CS2", "Dota2": "DOTA2", "R6S":"R6S", "Valorant": "Valorant"}
            markup = await for_tournaments(disciplines[tournament_discipline], tournament_tier, call.message.chat.id, discipline_dict[tournament_discipline])
            await bot.edit_message_text(f"Вы подписались на уведомления о матчах {tournament_tier} тира на {tournament_name} по {tournament_discipline}", chat_id=call.message.chat.id,
                                        message_id=call.message.message_id, reply_markup=markup.as_markup())
        else:
            markup = await delete_notification(tournament_name + "+s" if call.data.split("+")[-2] == "s" else tournament_name, discipline_id)
            await bot.edit_message_text(
                f"Вы хотите удалить турнир {tournament_tier} тира по {tournament_discipline} - {tournament_name} из своих оповещений?",
                chat_id=call.message.chat.id, message_id=call.message.message_id,
                reply_markup=markup)
    else:
        discipline_dict = {"Apex Legends": "Apex Legends", "CS2": "CS2", "Dota2": "DOTA2", "R6S":"R6S","Valorant": "Valorant"}
        await update_user_tournaments(call.message.chat.id, tournament_id)
        markup = await for_tournaments(disciplines[tournament_discipline], tournament_tier, call.message.chat.id, discipline_dict[tournament_discipline])
        await bot.edit_message_text(
            f"Вы подписались на уведомления о матчах на турнире {tournament_tier} тира {tournament_name} по {tournament_discipline}",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id, reply_markup=markup.as_markup())


# Обработка в случае случайного нажатия на кнопку
@dispatcher.callback_query(F.data.startswith("Mistake"))
async def mistake_remove(call: CallbackQuery):
    global disciplines
    if call.data.split("+")[-1] in ["1", "2", "3", "4", "5"]:
        tournament = await select_tournament_by_name_and_discipline(call.data.split("+")[1], int(call.data.split("+")[-1]))
    else:
        tournament = await select_tournament_by_name(call.data.split("+")[1])
    tournament_discipline = await select_game_by_id(int(tournament[0].to_dict()["GameID"]))
    tournament_discipline = str(tournament_discipline[0].Name)
    tournament_tier = tournament[0].to_dict()["Tier"]
    discipline_dict = {"Apex Legends": "Apex Legends", "CS2": "CS2", "Dota2": "DOTA2", "R6S":"R6S","Valorant": "Valorant"}
    if call.data.split("+")[-2] != "s":
        markup = await for_tournaments(disciplines[tournament_discipline],
                                       tournament_tier, call.message.chat.id,
                                       discipline_dict[tournament_discipline])
        await bot.edit_message_text(
            f"Вы выбрали тир {tournament_tier} турниров по {tournament_discipline}",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id, reply_markup=markup.as_markup())
    else:
        page = int(call.data.split("+")[-3])
        user_tournaments_ids = await select_user_tournaments(call.message.chat.id)
        if len(user_tournaments_ids[0]) > 1:
            user_tournaments_ids = list(map(int, user_tournaments_ids[0].split(',')))
            user_tournaments = []
            for i in user_tournaments_ids:
                tournament = await select_tournaments_by_id(i)
                user_tournaments.append([tournament[0].to_dict()["Name"], tournament[0].to_dict()["GameID"]])
            subs_keyboard = await subscriptions(user_tournaments, page)
            await bot.edit_message_text(f"Ваши выбранные подписки", chat_id=call.message.chat.id,
                                        message_id=call.message.message_id, reply_markup=subs_keyboard.as_markup())
        else:
            user_tournaments = []
            subs_keyboard = await subscriptions(user_tournaments, page)
            await bot.edit_message_text(f"Ваши выбранные подписки", chat_id=call.message.chat.id,
                                        message_id=call.message.message_id, reply_markup=subs_keyboard.as_markup())

# Обработка при нажатии на кнопку удалить подписку
@dispatcher.callback_query(F.data.startswith("Delete"))
async def delete_from_subs(call: CallbackQuery):
    global disciplines
    tournaments_selected = await select_user_tournaments(call.message.chat.id)
    tournament_id_to_delete = await select_tournament_by_name_and_discipline(call.data.split('+')[1], int(call.data.split("+")[-1]))
    tournament_id_to_delete = str(tournament_id_to_delete[0].to_dict()['TournamentID'])
    tournaments_selected = tournaments_selected[0].split(',') if len(tournaments_selected[0]) > 1 else []
    if len(tournaments_selected) >= 2:
        if tournaments_selected[0] != '':
            tournaments_selected.remove(tournament_id_to_delete)
            await update_user_tournaments(call.message.chat.id,
                                          ",".join(tournaments_selected))
        else:
            tournaments_selected.remove(tournament_id_to_delete)
            await update_user_tournaments(call.message.chat.id,
                                          ",".join(tournaments_selected[1:]))
    else:
        await update_user_tournaments(call.message.chat.id, '')
    discipline_dict = {"Apex Legends": "Apex Legends", "CS2": "CS2", "Dota2": "DOTA2", "R6S":"R6S","Valorant": "Valorant"}
    tournament = await select_tournament_by_name_and_discipline(call.data.split('+')[1], int(call.data.split("+")[-1]))
    tournament_discipline = await select_game_by_id(int(tournament[0].to_dict()["GameID"]))
    tournament_discipline = str(tournament_discipline[0].Name)
    tournament_tier = tournament[0].to_dict()["Tier"]
    if call.data.split("+")[-2] != "s":
        markup = await for_tournaments(disciplines[tournament_discipline],
                                       tournament_tier, call.message.chat.id,
                                       discipline_dict[tournament_discipline])
        await bot.edit_message_text(
            f"Вы выбрали тир {tournament_tier} турниров по {tournament_discipline}",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id, reply_markup=markup.as_markup())
    else:
        call.data.split("+")
        page = int(call.data.split("+")[-3])
        user_tournaments_ids = await select_user_tournaments(call.message.chat.id)
        if len(user_tournaments_ids[0]) > 1:
            user_tournaments_ids = list(map(int, user_tournaments_ids[0].split(',')))
            user_tournaments = []
            for i in user_tournaments_ids:
                tournament = await select_tournaments_by_id(i)
                user_tournaments.append([tournament[0].to_dict()["Name"], tournament[0].to_dict()["GameID"]])
            subs_keyboard = await subscriptions(user_tournaments, page)
            await bot.edit_message_text(f"Ваши выбранные подписки", chat_id=call.message.chat.id,
                                        message_id=call.message.message_id, reply_markup=subs_keyboard.as_markup())
        else:
            user_tournaments = []
            subs_keyboard = await subscriptions(user_tournaments, page)
            await bot.edit_message_text(f"Ваши выбранные подписки", chat_id=call.message.chat.id,
                                        message_id=call.message.message_id, reply_markup=subs_keyboard.as_markup())


async def main():
    global dispatcher, apex_tournaments, cs_tournaments, dota_tournaments, r6s_tournaments, valorant_tournaments, disciplines
    apex_tournaments = await apex.get_tournament()
    cs_tournaments = await cs.get_tournament()
    dota_tournaments = await dota2.get_tournament()
    r6s_tournaments = await r6s.get_tournament()
    valorant_tournaments = await valorant.get_tournament()
    disciplines = {"Apex Legends": apex_tournaments, "CS2": cs_tournaments, "Dota2": dota_tournaments,
                   "R6S": r6s_tournaments, "Valorant": valorant_tournaments}
    scheduler = AsyncIOScheduler(timezone="Asia/Yekaterinburg")
    scheduler.add_job(check, trigger="interval", seconds=60)
    scheduler.add_job(update_db, trigger="cron", hour=6, minute=00, start_date=datetime.now())
    scheduler.start()
    await dispatcher.start_polling(bot)

if __name__ == "__main__":
    bot = Bot(token=Config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s')
    logger = logging.getLogger(__name__)
    # First initialization with startup
    appname = "TNB/1.0(alexm.2005@mail.ru)"

    apex = Apex(appname=appname, game="apexlegends", discipline_id=1, game_name="Apex Legends")
    cs = CS(appname=appname, game="counterstrike", discipline_id=2, game_name="CS2")
    dota2 = DOTA2(appname=appname, game="dota2", discipline_id=3, game_name="Dota2")
    r6s = R6S(appname=appname, game="rainbowsix", discipline_id=4, game_name="R6S")
    valorant = Valorant(appname=appname, game="valorant", discipline_id=5, game_name="Valorant")
    apex_tournaments = []
    cs_tournaments = []
    dota_tournaments = []
    r6s_tournaments = []
    valorant_tournaments = []
    disciplines = {"Apex Legends": apex_tournaments, "CS2": cs_tournaments, "Dota2": dota_tournaments,
                   "R6S": r6s_tournaments, "Valorant": valorant_tournaments}
    asyncio.run(main())