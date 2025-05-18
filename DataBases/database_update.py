import asyncio
from DataBases.update_methods import update_matches
from DataBases.select_methods import select_all_matches, select_tournament_by_name, select_matches_by_id
from DataBases.delete_methods import delete_match
from DataBases.add_methods import add_match
from Disciplines.Apex import Apex
from Disciplines.CS2 import CS
from Disciplines.Dota2 import DOTA2
from Disciplines.R6S import R6S
from Disciplines.Valorant import Valorant
import datetime
from datetime import datetime
from dateutil import parser


async def update_db():
    appname = "TNB/1.0(alexm.2005@mail.ru)"
    tournaments = await get_tournament_db()
    for tournament in tournaments:
        if datetime.today() > parser.parse(tournament.to_dict()['Time']):
            await delete_match(tournament['TournamentID'])
    apex = Apex(appname=appname, game="apexlegends", discipline_id=1, game_name="Apex Legends")
    cs = CS(appname=appname, game="counterstrike", discipline_id=2, game_name="CS2")
    dota2 = DOTA2(appname=appname, game="dota2", discipline_id=3, game_name="Dota2")
    r6s = R6S(appname=appname, game="rainbowsix", discipline_id=4, game_name="R6S")
    valorant = Valorant(appname=appname, game="valorant", discipline_id=5, game_name="Valorant")
    dota_matches = await dota2.get_matches()
    for match in dota_matches:
        matches_id = await select_tournament_by_name(match['tournament'])
        match_id = 0
        for i in matches_id:
            match_id = i.TournamentID
        info = await select_matches_by_id(match_id)
        if len(info) == 0:
            await add_match({"TournamentID": match_id, "GameID": 3, "Time": match["time"]})
        elif match_id != 0:
            await update_matches(tournamentid=match_id,gameid=3,time=match['time'])
    await asyncio.sleep(60)
    cs_matches = await cs.get_matches()
    for match in cs_matches:
        matches_id = await select_tournament_by_name(match['tournament'])
        match_id = 0
        for i in matches_id:
            match_id = i.TournamentID
        info = await select_matches_by_id(match_id)
        if len(info) == 0:
            await add_match({"TournamentID": match_id, "GameID": 2, "Time": match["time"]})
        elif match_id != 0:
            await update_matches(tournamentid=match_id, gameid=2, time=match['time'])
    await asyncio.sleep(60)
    apex_matches = await apex.get_matches()
    for match in apex_matches:
        matches_id = await select_tournament_by_name(match['tournament'])
        match_id = 0
        for i in matches_id:
            match_id = i.TournamentID
        info = await select_matches_by_id(match_id)
        if len(info) == 0:
            await add_match(match_data={"TournamentsID": match_id, "GamesID": 1, "Time": match["time"]})
        elif match_id != 0:
            await update_matches(tournamentid=match_id, gameid=1, time=match['time'])
    await asyncio.sleep(60)
    r6s_matches = await r6s.get_matches()
    for match in r6s_matches:
        matches_id = await select_tournament_by_name(match['tournament'])
        match_id = 0
        for i in matches_id:
            match_id = i.TournamentID
        info = await select_matches_by_id(match_id)
        if len(info) == 0:
            await add_match({"TournamentID": match_id, "GameID": 4, "Time": match["time"]})
        elif match_id != 0:
            await update_matches(tournamentid=match_id, gameid=4, time=match['time'])
    await asyncio.sleep(60)
    valorant = await valorant.get_matches()
    for match in valorant:
        matches_id = await select_tournament_by_name(match['tournament'])
        match_id = 0
        for i in matches_id:
            match_id = i.TournamentID
        info = await select_matches_by_id(match_id)
        if len(info) == 0:
            await add_match({"TournamentID": match_id, "GameID": 5, "Time": match["time"]})
        elif match_id != 0:
            await update_matches(tournamentid=match_id, gameid=5, time=match['time'])
    await asyncio.sleep(60)

async def get_tournament_db():
    tournaments = await select_all_matches()
    return tournaments