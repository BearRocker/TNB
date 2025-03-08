import aiogram.exceptions
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from DataBases.add_methods import add_user
from DataBases.update_methods import update_user_tournaments
from Disciplines.Apex import Apex
from Disciplines.CS2 import CS
from Disciplines.Dota2 import DOTA2
import logging
import asyncio
import re
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart, Command
from DataBases.select_methods import select_user_by_id, select_user_tournaments, select_tournament_by_name, select_users
from DataBases import database_update
from datetime import datetime
import aioschedule
from dateutil import parser
from datetime import timedelta
import Config
from keyboard_methods import start_sub_check, start_menu,search_for_tier,subscriptions, for_tournaments, choose_discipline, delete_notification


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
bot = Bot(token=Config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dispatcher = Dispatcher()


# First initialization with startup
apex = Apex(appname="TNB", game="apexlegends", discipline_id=1, game_name="Apex Legends")
cs = CS(appname="TNB", game="counterstrike", discipline_id=2, game_name="CS2")
dota2 = DOTA2(appname="TNB", game="dota2", discipline_id=3, game_name="Dota2")
apex_tournaments = []
cs_tournaments = []
dota_tournaments = []
disciplines = {'Apex Legends': apex_tournaments, 'Counter Strike': cs_tournaments, 'Dota 2': dota_tournaments}


async def check(message): # Проверка времени до начала матча и на проверку прошедших турниров в подписках
    # Checking time before start matches and for checking concluded tournaments in subs
    users = await select_users()
    all_tournaments = []
    for cs_t in cs_tournaments:
        all_tournaments.append(cs_t["tournament"])
    for dota_t in dota_tournaments:
        all_tournaments.append(dota_t["tournament"])
    for a_t in apex_tournaments:
        all_tournaments.append(a_t["tournament"])
    tournaments_soon = await database_update.get_tournament_db()
    for i in range(len(all_tournaments)):
        a = await select_tournament_by_name(all_tournaments[i])
        all_tournaments[i] = str(a[0].to_dict()['TournamentID'])
    for user in users:
        tournaments = user.TournamentsID
        tournaments_deprived = tournaments.split(',')
        res = tournaments.split(',')
        for tournament in tournaments_deprived:
            for tournament_soon in tournaments_soon:
                if tournament[1:] in tournament_soon:
                    today = datetime.today()
                    if (today + timedelta(hours=int(user[2].split()[0]))).strftime('%y-%m-%d %H:%M') == parser.parse(tournament_soon[-1]).strftime('%y-%m-%d %H:%M'):
                        await bot.send_message(chat_id=user[0], text=f"Уведомление за 1 час о начале матчей на {tournament[1:]}")
                    elif today.strftime('%y-%m-%d %H:%M') == parser.parse(tournament_soon[-1]).strftime('%y-%m-%d %H:%M'):
                        await message.answer(chat_id=user[0],
                                               text=f"Уведомление о начале матчей на {tournament[1:]}")
            if tournament not in all_tournaments:
                res.remove(tournament)
                await update_user_tournaments(user.ChatID, ','.join(res))


async def update_db():  # Обновление ДБ каждый день в 6 утра по Пермскому
    # Updating DB every day at 6:00 +2 MSK
    global apex_tournaments, cs_tournaments, dota_tournaments, disciplines
    if datetime.now().hour == 6 and datetime.now().minute == 0 and datetime.now().second == 0:
        # await bot.send_message(chat_id=Config.bot_channel_id, text='Бот ушёл на обновление баз данных будет доступен через 10 минут') уже не нужно, оставил на всякий
        apex_tournaments = await apex.get_tournament()
        cs_tournaments = await cs.get_tournament()
        dota_tournaments = await dota2.get_tournament()
        disciplines = {'Apex Legends': apex_tournaments, 'Counter Strike': cs_tournaments, 'Dota 2': dota_tournaments}
        await database_update.update_db()


async def update_db_command():
    global apex_tournaments, cs_tournaments, dota_tournaments, disciplines
    apex_tournaments = await apex.get_tournament()
    cs_tournaments = await cs.get_tournament()
    dota_tournaments = await dota2.get_tournament()
    disciplines = {'Apex Legends': apex_tournaments, 'Counter Strike': cs_tournaments, 'Dota 2': dota_tournaments}
    await database_update.update_db()

# Starting up every minute check
aioschedule.every(60).seconds.do(check)
aioschedule.every(1).seconds.do(update_db)


# "/start" message
@dispatcher.message(CommandStart())
async def start_message(message: Message):
    keyboard = await start_sub_check()
    await bot.send_message(chat_id=message.chat.id,text='Привет, это бот для уведомлений о киберспортивных событиях. Для начала работы подпишись на телеграмм канал.',
                           reply_markup=keyboard)


# Checking is user subbed
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


@dispatcher.message(Command('b01cf5cb16d9d3e487d58ab8297dc5e6'))
async def upgrade_people_upgrade(message: Message):
    await message.answer('Let\'s go gambling...')
    await update_db_command()


@dispatcher.callback_query(F.data == "Choose discipline")
async def choose_discipline_callback(call: CallbackQuery):
    markup = await choose_discipline()
    await bot.edit_message_text(chat_id=call.message.chat.id, text="Выбирай дисциплину", reply_markup=markup, message_id=call.message.message_id)


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
        await bot.send_message(chat_id=call.message.chat.id, text="Выбирай что-то из этого", reply_markup=markup)
        user_exists = await select_user_by_id(call.message.chat.id)
        if len(user_exists) == 0:
            await add_user({'ChatID': call.message.chat.id, 'TournamentsID': '', "Settings": '1 hour'})
        else:
            pass


@dispatcher.callback_query(F.data.startswith("Apex"))
async def Apex_tiers(call: CallbackQuery):
    tier = call.data.split('|')[1] if len(call.data.split('|'))>1 else None # Tier = S-Tier, A-Tier, B-Tier
    if tier:
        if "Back" not in tier:
            markup = await for_tournaments(apex_tournaments, tier, call.message.chat.id, 'Apex')
            await bot.edit_message_text(f"Вы выбрали тир {tier} турниров по Apex Legends", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup.as_markup())
    else:
        markup = await search_for_tier('Apex', ["S-Tier", "A-Tier", "B-Tier"])
        await bot.edit_message_text("Вы выбрали дисциплину Apex Legends", chat_id=call.message.chat.id,
                                    message_id=call.message.message_id, reply_markup=markup)

@dispatcher.callback_query(F.data.contains('Back'))
async def back_to(call: CallbackQuery):
    discipline = call.data.split("|")[1] if len(call.data.split("|"))>1 else None
    print(discipline)
    if discipline == "Apex":
        markup = await search_for_tier('Apex', ["S-Tier", "A-Tier", "B-Tier"])
        await bot.edit_message_text("Вы выбрали дисциплину Apex Legends", chat_id=call.message.chat.id,
                                    message_id=call.message.message_id, reply_markup=markup)
    elif discipline == "CS2":
        markup = await search_for_tier('CS2', ["S-Tier", "A-Tier", "B-Tier"])
        await bot.edit_message_text("Вы выбрали дисциплину CS2", chat_id=call.message.chat.id,
                                    message_id=call.message.message_id, reply_markup=markup)
    elif discipline == "DOTA2":
        markup = await search_for_tier('DOTA2', ["Tier 1", "Tier 2", "Tier 3"])
        await bot.edit_message_text("Вы выбрали дисциплину Dota 2", chat_id=call.message.chat.id,
                                    message_id=call.message.message_id, reply_markup=markup)
    else:
        markup = await choose_discipline()
        await bot.edit_message_text("Выбирай дисциплину", chat_id=call.message.chat.id,
                                    message_id=call.message.message_id, reply_markup=markup)



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


# markup = await for_tournaments(apex_tournaments, "S-Tier", call.message.chat.id)
#             await bot.edit_message_text(
#                 text,
#                 chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)


@dispatcher.callback_query(F.data.startswith('t+'))
async def add_tournament_to_db(call: CallbackQuery):
    global disciplines
    tournament = call.data.split("+")[-1]
    tournament = await select_tournament_by_name(tournament)
    tournament = tournament[0].to_dict()['Name']
    tournament_ids = await select_tournament_by_name(tournament)
    tournament_ids = str(tournament_ids[0].TournamentID)
    tournaments_selected = await select_user_tournaments(call.message.chat.id)
    if tournaments_selected[0] != '':
        if tournament_ids not in tournaments_selected[0].split(','):
            tournament_id = await select_tournament_by_name(tournament)
            tournament_id = str(tournament_id[0].TournamentID)
            await update_user_tournaments(call.message.chat.id, tournaments_selected[0] + "," + tournament_id)
            tiers = ["\\bS\\b", "\\bA\\b", "\\bB\\b"]
            pattern_discipline = ['\\bApex Legends\\b', '\\bCounter Strike\\b', '\\bDota 2\\b']
            discipline_res = {"Apex Legends": "Apex", "Counter Strike": "CS2", "Dota 2": "DOTA2"}
            message_text = call.message.text
            founded_tier = ''
            discipline = ''
            for tier in tiers:
                find_tier = re.findall(tier, call.message.text)
                if len(find_tier) != 0:
                    founded_tier = find_tier[0]
            for p in pattern_discipline:
                find_discipline = re.findall(p, message_text)
                if len(find_discipline) != 0:
                    discipline = find_discipline[0]
            markup = await for_tournaments(disciplines[discipline], founded_tier+"-Tier" if founded_tier in ["S", "A", "B"] else "Tier " + founded_tier, call.message.chat.id, discipline_res[discipline])
            await bot.edit_message_text(f"Вы подписались на уведомления о матчах на турнире {founded_tier} тира {tournament} по {discipline}", chat_id=call.message.chat.id,
                                        message_id=call.message.message_id, reply_markup=markup.as_markup())
        else:
            markup = await delete_notification(tournament)
            message_text = call.message.text
            pattern_discipline = ['\\bApex Legends\\b', '\\bCounter Strike\\b', '\\bDota 2\\b']
            pattern_tier = ['\\bS\\b', '\\bA\\b', '\\bB\\b']
            for p in pattern_discipline:
                find_discipline = re.findall(p, message_text)
                if len(find_discipline) != 0:
                    for pt in pattern_tier:
                        find_tier = re.findall(pt, message_text)
                        if len(find_tier) != 0:
                            await bot.edit_message_text(
                                f"Вы хотите удалить турнир {find_tier[0]} тира по {find_discipline[0]} - {tournament} из своих оповещений?",
                                chat_id=call.message.chat.id, message_id=call.message.message_id,
                                reply_markup=markup)
    else:
        discipline_res = {"Apex Legends": "Apex", "Counter Strike": "CS2", "Dota 2": "DOTA2"}
        tournament_id = await select_tournament_by_name(tournament)
        tournament_id = str(tournament_id[0].TournamentID)
        await update_user_tournaments(call.message.chat.id, tournament_id)
        tiers = ["\\bS\\b", "\\bA\\b", "\\bB\\b"]
        pattern_discipline = ['\\bApex Legends\\b', '\\bCounter Strike\\b', '\\bDota 2\\b']
        message_text = call.message.text
        founded_tier = ''
        discipline = ''
        for tier in tiers:
            find_tier = re.findall(tier, call.message.text)
            if len(find_tier) != 0:
                founded_tier = find_tier[0]
        for p in pattern_discipline:
            find_discipline = re.findall(p, message_text)
            if len(find_discipline) != 0:
                discipline = find_discipline[0]
        markup = await for_tournaments(disciplines[discipline], founded_tier+"-Tier" if founded_tier in ["S", "A", "B"] else "Tier " + founded_tier, call.message.chat.id, discipline_res[discipline])
        await bot.edit_message_text(
            f"Вы подписались на уведомления о матчах на турнире {founded_tier} тира {tournament} по {discipline}",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id, reply_markup=markup.as_markup())


@dispatcher.callback_query(F.data == "Mistake")
async def mistake_remove(call: CallbackQuery):
    tiers = ["\\bS\\b", "\\bA\\b", "\\bB\\b"]
    global disciplines
    disciplines_list = ["Apex Legends", "Counter Strike", "Dota 2"]
    discipline_res = {"Apex Legends": "Apex", "Counter Strike": "CS2", "Dota 2": "DOTA2"}
    for tier in tiers:
        find_tier = re.findall(tier, call.message.text)
        if len(find_tier) != 0:
            for discipline in disciplines_list:
                if discipline in call.message.text:
                    markup = await for_tournaments(disciplines[discipline], find_tier[0]+"-Tier" if find_tier[0] in ["S", "A", "B"] else "Tier " + find_tier[0], call.message.chat.id,
                                                   discipline_res[discipline])
                    await bot.edit_message_text(
                        f"Вы выбрали тир {find_tier[0]} турниров по Apex Legends",
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id, reply_markup=markup.as_markup())

@dispatcher.callback_query(F.data.startswith("Delete"))
async def delete_from_subs(call: CallbackQuery):
    global disciplines
    tournaments_selected = await select_user_tournaments(call.message.chat.id)
    tournament_id_to_delete = await select_tournament_by_name(call.data.split('+')[1])
    tournament_id_to_delete = str(tournament_id_to_delete[0].to_dict()['TournamentID'])
    tournaments_selected = tournaments_selected[0].split(',') if len(tournaments_selected[0]) > 1 else []
    if len(tournaments_selected) >= 2:
        tournaments_selected.remove(tournament_id_to_delete)
        await update_user_tournaments(call.message.chat.id,
                                      ",".join(tournaments_selected))
    else:
        await update_user_tournaments(call.message.chat.id, '')
    tiers = ["\\bS\\b", "\\bA\\b", "\\bB\\b"]
    disciplines_list = ["Apex Legends", "Counter Strike", "Dota 2"]
    discipline_res = {"Apex Legends": "Apex", "Counter Strike": "CS2", "Dota 2": "DOTA2"}
    for tier in tiers:
        find_tier = re.findall(tier, call.message.text)
        if len(find_tier) != 0:
            for discipline in disciplines_list:
                if discipline in call.message.text:
                    markup = await for_tournaments(disciplines[discipline], find_tier[0]+"-Tier" if find_tier[0] in ["S", "A", "B"] else "Tier " + find_tier[0], call.message.chat.id,
                                                   discipline_res[discipline])
                    await bot.edit_message_text(
                        f"Вы выбрали тир {find_tier[0]} турниров по Apex Legends",
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id, reply_markup=markup.as_markup())


# # Main bot functions
# @bot.callback_query_handler(func=lambda call: True)
# async def callback_worker(call):
#     global apex_tournaments, cs_tournaments, dota_tournaments
#     is_subbed = await is_sub(call.from_user.id)
#     if is_subbed:  # Check for sub
#         if call.data == "Проверить подписку":
#             sub = await is_sub(call.from_user.id)
#             if not sub:
#                 keyboard = types.InlineKeyboardMarkup()
#                 key_tg = types.InlineKeyboardButton(text='ТГ канал', url="https://t.me/+n-81CI4xTelhZjgy")
#                 keyboard.add(key_tg)
#                 key_check = types.InlineKeyboardButton(text="Проверить подписку", callback_data="Проверить подписку")
#                 keyboard.add(key_check)
#                 await bot.edit_message_text("Вы не подписаны на канал, для работы бота подпишитесь на канал.",
#                                             message_id=call.message.message_id, chat_id=call.message.chat.id,
#                                             reply_markup=keyboard)
#             else:
#                 markup = await start_menu()
#                 await bot.edit_message_text("Отлично ты подписан!", message_id=call.message.message_id,
#                                             chat_id=call.message.chat.id)
#                 await bot.send_message(chat_id=call.message.chat.id, text="Выбирай что-то из этого", reply_markup=markup)
#                 user_exists = await select_user_by_id(call.message.chat.id)
#                 if len(user_exists) == 0:
#                     await add_user({'ChatID': call.message.chat.id, 'TournamentsID': '', "Settings": '1 hour'})
#                 else:
#                     pass
#         if call.data == "choose discipline":  # Menu of choosing discipline
#             markup = await choose_discipline()
#             await bot.edit_message_text(chat_id=call.message.chat.id, text="Выбирай дисциплину", reply_markup=markup, message_id=call.message.message_id)
#         if call.data == "Subs":  # Show user his subs
#             markup = await subscriptions()
#             tournaments = await select_user_tournaments(call.message.chat.id)
#             tournaments_split = tournaments[0].split(',')
#             text = 'Выбранные подписки\n'
#             if len(tournaments_split) > 1 or tournaments_split[0] != '':
#                 for i in tournaments_split:
#                     tournament = await select_tournaments_by_id(int(i))
#                     tournament = tournament[0]
#                     if i != '':
#                         text += tournament + '\n'
#             else:
#                 text += 'Вы не подписаны ни на один турнир'
#             await bot.edit_message_text(chat_id=call.message.chat.id, text=text, reply_markup=markup, message_id=call.message.message_id)
#         if call.data == "Back" or call.data == "Back disciplines":  # Return to discipline choose
#             markup = await choose_discipline()
#             await bot.edit_message_text("Выбирай дисциплину", chat_id=call.message.chat.id,
#                                         message_id=call.message.message_id, reply_markup=markup)
#         if call.data == "Apex":  # Apex tournaments tiers
#             markup = await search_for_tier()
#             await bot.edit_message_text("Вы выбрали дисциплину Apex Legends", chat_id=call.message.chat.id,
#                                         message_id=call.message.message_id, reply_markup=markup)
#         if call.data == "CS":  # CS tournaments tiers
#             markup = await search_for_tier()
#             await bot.edit_message_text("Вы выбрали дисциплину Counter Strike", chat_id=call.message.chat.id,
#                                         message_id=call.message.message_id, reply_markup=markup)
#         if call.data == "Dota 2":  # Dota tournaments tiers
#             markup = await search_for_tier()
#             await bot.edit_message_text("Вы выбрали дисциплину Dota 2", chat_id=call.message.chat.id,
#                                         message_id=call.message.message_id, reply_markup=markup)
#         if call.data == "S":  # S-Tier(1-Tier) tournaments
#             if "Apex" in call.message.text:
#                 markup = await for_tournaments(apex_tournaments, "S-Tier", call.message.chat.id)
#                 await bot.edit_message_text("Вы выбрали тир S турниров по Apex Legends", chat_id=call.message.chat.id,
#                                             message_id=call.message.message_id, reply_markup=markup)
#             if "Counter Strike" in call.message.text:
#                 markup = await for_tournaments(cs_tournaments, "S-Tier", call.message.chat.id)
#                 await bot.edit_message_text("Вы выбрали тир S турниров по Counter Strike", chat_id=call.message.chat.id,
#                                             message_id=call.message.message_id, reply_markup=markup)
#             if "Dota 2" in call.message.text:
#                 markup = await for_tournaments(dota_tournaments, "Tier 1", call.message.chat.id)
#                 await bot.edit_message_text("Вы выбрали тир S турниров по Dota 2", chat_id=call.message.chat.id,
#                                             message_id=call.message.message_id, reply_markup=markup)
#         if call.data == "A":  # A-Tier(2-Tier) tournaments
#             if "Apex" in call.message.text:
#                 markup = await for_tournaments(apex_tournaments, "A-Tier", call.message.chat.id)
#                 await bot.edit_message_text("Вы выбрали тир A турниров по Apex Legends", chat_id=call.message.chat.id,
#                                             message_id=call.message.message_id, reply_markup=markup)
#             if "Counter Strike" in call.message.text:
#                 markup = await for_tournaments(cs_tournaments, "A-Tier", call.message.chat.id)
#                 await bot.edit_message_text("Вы выбрали тир A турниров по Counter Strike", chat_id=call.message.chat.id,
#                                             message_id=call.message.message_id, reply_markup=markup)
#             if "Dota 2" in call.message.text:
#                 markup = await for_tournaments(dota_tournaments, "Tier 2", call.message.chat.id)
#                 await bot.edit_message_text("Вы выбрали тир A турниров по Dota 2", chat_id=call.message.chat.id,
#                                             message_id=call.message.message_id, reply_markup=markup)
#         if call.data == "B":  # B-Tier(3-Tier) tournaments
#             if "Apex" in call.message.text:
#                 markup = await for_tournaments(apex_tournaments, "B-Tier", call.message.chat.id)
#                 await bot.edit_message_text("Вы выбрали тир B турниров по Apex Legends", chat_id=call.message.chat.id,
#                                             message_id=call.message.message_id, reply_markup=markup)
#             if "Counter Strike" in call.message.text:
#                 markup = await for_tournaments(cs_tournaments, "B-Tier", call.message.chat.id)
#                 await bot.edit_message_text("Вы выбрали тир B турниров по Counter Strike", chat_id=call.message.chat.id,
#                                             message_id=call.message.message_id, reply_markup=markup)
#             if "Dota 2" in call.message.text:
#                 markup = await for_tournaments(dota_tournaments, "Tier 3", call.message.chat.id)
#                 await bot.edit_message_text("Вы выбрали тир B турниров по Dota 2", chat_id=call.message.chat.id,
#                                             message_id=call.message.message_id, reply_markup=markup)
#         if call.data == "Back tier":  # Back to tier menu
#             if "Apex" in call.message.text:
#                 markup = await search_for_tier()
#                 await bot.edit_message_text("Вы выбрали дисциплину Apex Legends", chat_id=call.message.chat.id,
#                                             message_id=call.message.message_id, reply_markup=markup)
#             if "Counter Strike" in call.message.text:
#                 markup = await search_for_tier()
#                 await bot.edit_message_text("Вы выбрали дисциплину Counter Strike", chat_id=call.message.chat.id,
#                                             message_id=call.message.message_id, reply_markup=markup)
#             if "Dota 2" in call.message.text:
#                 markup = await search_for_tier()
#                 await bot.edit_message_text("Вы выбрали дисциплину Dota 2", chat_id=call.message.chat.id,
#                                             message_id=call.message.message_id, reply_markup=markup)
#         if "{" in call.data:  # Main for subbing and adding to DB users tournaments mostly I don't give a fuck what's going on here anymore
#             tournament = call.data.split("+")[-1]
#             tournament = await select_tournament_by_name(tournament)
#             tournament = tournament[0].to_dict()['Name']
#             tournament_ids = await select_tournament_by_name(tournament)
#             tournament_ids = str(tournament_ids[0].TournamentID)
#             tournaments_selected = await select_user_tournaments(call.message.chat.id)
#             if tournaments_selected[0] != '':
#                 if tournament_ids not in tournaments_selected[0].split(','):
#                     tournament = await select_tournament_by_name(tournament)
#                     tournament = str(tournament[0].TournamentID)
#                     await update_user_tournaments(call.message.chat.id, tournaments_selected[0] + "," + tournament)
#                     tiers = ["\\bS\\b", "\\bA\\b", "\\bB\\b"]
#                     pattern_discipline = ['\\bApex Legends\\b', '\\bCounter Strike\\b', '\\bDota 2\\b']
#                     message_text = call.message.text
#                     founded_tier = ''
#                     discipline = ''
#                     for tier in tiers:
#                         find_tier = re.findall(tier, call.message.text)
#                         if len(find_tier) != 0:
#                             founded_tier = find_tier[0]
#                     for p in pattern_discipline:
#                         find_discipline = re.findall(p, message_text)
#                         if len(find_discipline) != 0:
#                             discipline = find_discipline[0]
#                     await discipline_tier(call, founded_tier, discipline, f"Вы подписались на уведомления о матчах на турнире {founded_tier} тира {tournament} по {discipline}")
#                 else:
#                     markup = await delete_notification(tournament)
#                     message_text = call.message.text
#                     pattern_discipline = ['\\bApex Legends\\b', '\\bCounter Strike\\b', '\\bDota 2\\b']
#                     pattern_tier = ['\\bS\\b', '\\bA\\b', '\\bB\\b']
#                     for p in pattern_discipline:
#                         find_discipline = re.findall(p, message_text)
#                         if len(find_discipline) != 0:
#                             for pt in pattern_tier:
#                                 find_tier = re.findall(pt, message_text)
#                                 if len(find_tier) != 0:
#                                     await bot.edit_message_text(
#                                         f"Вы хотите удалить турнир {find_tier[0]} тира по {find_discipline[0]} - {tournament} из своих оповещений?",
#                                         chat_id=call.message.chat.id, message_id=call.message.message_id,
#                                         reply_markup=markup)
#             else:
#                 tournament_id = await select_tournament_by_name(tournament)
#                 tournament_id = str(tournament_id[0].TournamentID)
#                 await update_user_tournaments(call.message.chat.id, tournament_id)
#                 tiers = ["\\bS\\b", "\\bA\\b", "\\bB\\b"]
#                 pattern_discipline = ['\\bApex Legends\\b', '\\bCounter Strike\\b', '\\bDota 2\\b']
#                 message_text = call.message.text
#                 founded_tier = ''
#                 discipline = ''
#                 for tier in tiers:
#                     find_tier = re.findall(tier, call.message.text)
#                     if len(find_tier) != 0:
#                         founded_tier = find_tier[0]
#                 for p in pattern_discipline:
#                     find_discipline = re.findall(p, message_text)
#                     if len(find_discipline) != 0:
#                         discipline = find_discipline[0]
#                 await discipline_tier(call, founded_tier, discipline, f"Вы подписались на уведомления о матчах на турнире {founded_tier} тира {tournament} по {discipline}")
#         if "Delete" in call.data:  # Deleting tournament from user subs it seems readable
#             tournaments_selected = await select_user_tournaments(call.message.chat.id)
#             tournaments_selected = tournaments_selected[0].split(',') if len(tournaments_selected) > 1 else []
#             if len(tournaments_selected) >= 2:
#                 await update_user_tournaments(call.message.chat.id, tournaments_selected[0].replace(',' + call.data.split("+")[-1], ""))
#             else:
#                 await update_user_tournaments(call.message.chat.id, '')
#             tiers = ["\\bS\\b", "\\bA\\b", "\\bB\\b"]
#             disciplines = ["Apex Legends", "Counter Strike", "Dota 2"]
#             for tier in tiers:
#                 find_tier = re.findall(tier, call.message.text)
#                 if len(find_tier) != 0:
#                     for discipline in disciplines:
#                         if discipline in call.message.text:
#                             await discipline_tier(call, find_tier[0], discipline, f"Вы выбрали тир {find_tier[0]} турниров по Apex Legends")
#         if "Mistake" in call.data:  # If user missclicked or doubletapped and return to menu where he was wow it's really easy
#             tiers = ["\\bS\\b", "\\bA\\b", "\\bB\\b"]
#             disciplines = ["Apex Legends", "Counter Strike", "Dota 2"]
#             for tier in tiers:
#                 find_tier = re.findall(tier, call.message.text)
#                 if len(find_tier) != 0:
#                     for discipline in disciplines:
#                         if discipline in call.message.text:
#                             await discipline_tier(call, find_tier[0], discipline,
#                                                   f"Вы выбрали тир {find_tier[0]} турниров по Apex Legends")
#     else:
#         keyboard = types.InlineKeyboardMarkup()
#         key_tg = types.InlineKeyboardButton(text='ТГ канал', url="https://t.me/+n-81CI4xTelhZjgy")
#         keyboard.add(key_tg)
#         key_check = types.InlineKeyboardButton(text="Проверить подписку", callback_data="Проверить подписку")
#         keyboard.add(key_check)
#         await bot.edit_message_text("Вы не подписаны на канал, для работы бота подпишитесь на канал.",
#                                     message_id=call.message.message_id, chat_id=call.message.chat.id,
#                                     reply_markup=keyboard)
#
#
# async def discipline_tier(call, tier, discipline, text):  # Func which make's less repeating code when looking for tier and discipline
#     if tier == "S":
#         if discipline == "Apex Legends":
#             markup = await for_tournaments(apex_tournaments, "S-Tier", call.message.chat.id)
#             await bot.edit_message_text(
#                 text,
#                 chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
#         if discipline == "Counter Strike":
#             markup = await for_tournaments(cs_tournaments, "S-Tier", call.message.chat.id)
#             await bot.edit_message_text(
#                 text,
#                 chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
#         if discipline == "Dota 2":
#             markup = await for_tournaments(dota_tournaments, "Tier 1", call.message.chat.id)
#             await bot.edit_message_text(
#                 text,
#                 chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
#     if tier == "A":
#         if discipline == "Apex Legends":
#             markup = await for_tournaments(apex_tournaments, "A-Tier", call.message.chat.id)
#             await bot.edit_message_text(
#                 text,
#                 chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
#         if discipline == "Counter Strike":
#             markup = await for_tournaments(cs_tournaments, "A-Tier", call.message.chat.id)
#             await bot.edit_message_text(
#                 text,
#                 chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
#         if discipline == "Dota 2":
#             markup = await for_tournaments(dota_tournaments, "Tier 2", call.message.chat.id)
#             await bot.edit_message_text(
#                 text,
#                 chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
#     if tier == "B":
#         if discipline == "Apex Legends":
#             markup = await for_tournaments(apex_tournaments, "B-Tier", call.message.chat.id)
#             await bot.edit_message_text(
#                 text,
#                 chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
#         if discipline == "Counter Strike":
#             markup = await for_tournaments(cs_tournaments, "B-Tier", call.message.chat.id)
#             await bot.edit_message_text(
#                 text,
#                 chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
#         if discipline == "Dota 2":
#             markup = await for_tournaments(dota_tournaments, "Tier 3", call.message.chat.id)
#             await bot.edit_message_text(
#                 text,
#                 chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
#
#
async def scheduler():
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def main():
    global apex, cs, dota2, apex_tournaments, cs_tournaments, dota_tournaments, disciplines
    apex = Apex(appname="TNB", game="apexlegends", discipline_id=1, game_name="Apex Legends")
    cs = CS(appname="TNB", game="counterstrike", discipline_id=2, game_name="CS2")
    dota2 = DOTA2(appname="TNB", game="dota2", discipline_id=3, game_name="Dota2")
    apex_tournaments = await apex.get_tournament()
    cs_tournaments = await cs.get_tournament()
    dota_tournaments = await dota2.get_tournament()
    disciplines = {'Apex Legends': apex_tournaments, 'Counter Strike': cs_tournaments, 'Dota 2': dota_tournaments}
    await dispatcher.start_polling(bot)

asyncio.run(main())