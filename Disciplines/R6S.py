from datetime import datetime
from dateutil import parser
import pytz
from datetime import timedelta
import asyncio
from DataBases.delete_methods import delete_tournament
from DataBases.select_methods import select_tournaments, select_games
from DataBases.add_methods import add_tournament, add_games
from Disciplines.BaseDiscipline import Base


class R6S(Base):
    def __init__(self, appname, game, discipline_id, game_name):
        super().__init__(appname, game, discipline_id, game_name)

    async def get_tier(self, tier):
        tournaments = []
        tournaments_names = []
        soup1, __ = self.liquipedia.parse(tier)
        tables = soup1.find_all('div', class_="gridTable")
        tournaments_db = await select_tournaments()
        tournaments_db = {i.Name: i.GameID for i in tournaments_db}
        tournaments_db_names = []
        for k,v in tournaments_db.items():
            tournaments_db_names.append(k+str(v))
        for table in tables:
            rows = table.find_all('div', class_="gridRow")
            for row in rows:
                tournament = {}
                tournament_name = row.find("div", class_="gridCell Tournament Header")
                tournament_tier = row.find("div", class_="gridCell Tier Header")
                tournament_date = row.find("div", class_="gridCell EventDetails Date Header")
                tournament_prize = row.find("div", class_="gridCell EventDetails Prize Header")
                tournament_teamscount = row.find('div', class_="gridCell EventDetails PlayerNumber Header")
                tournament_place = row.find('span', class_="FlagText")
                tournament["tier"] = tier.split("_")[0]
                tournament["tournament"] = tournament_name.get_text().replace('\xa0', '')
                tournaments_names.append(tournament['tournament'])
                if self.is_today_before_date_range(tournament_date.get_text()):
                    tournament["date"] = tournament_date.get_text()
                else:
                    continue
                if tournament_prize:
                    tournament["prize"] = tournament_prize.get_text()
                else:
                    tournament["prize"] = 0
                if tournament_teamscount:
                    teams_on_tournament = tournament_teamscount.get_text()[0:3]
                    teams_on_tournament = teams_on_tournament.replace(u"\xa0", u"")
                else:
                    teams_on_tournament = ""
                if len(teams_on_tournament) >= 2:
                    tournament["teams_count"] = teams_on_tournament
                else:
                    tournament["teams_count"] = "idk"
                if tournament_place:
                    tournament["place"] = tournament_place.get_text()
                else:
                    tournament["place"] = row.find('div', class_="gridCell EventDetails Location Header").get_text()
                print(tournament['tournament'], tournament["date"])
                if tournament['tournament']+str(self.discipline_id) not in tournaments_db_names:
                    await add_tournament({"Prize": str(tournament['prize']), "TeamsCount": tournament["teams_count"],
                                          "Tier": tournament["tier"], "GameID": self.discipline_id,
                                          "Name": tournament['tournament'], "Date": tournament["date"],
                                          "Location": tournament["place"]})
                tournaments.append(tournament)
        return tournaments


    async def get_tournament(self):
        games = await select_games(self.game_name)
        if len(games) == 0:
            await add_games({"GameID": self.discipline_id, "Name": self.game_name})
        tournaments = []
        tournaments_names = []
        tournaments_db = await select_tournaments()
        tournaments_db = [[i.Name, i.GameID] for i in tournaments_db]
        tournaments_db_names = []
        for i in tournaments_db:
            tournaments_db_names.append(i[0])
        s_tier = await self.get_tier("S-Tier_Tournaments")
        a_tier = await self.get_tier("A-Tier_Tournaments")
        b_tier = await self.get_tier("B-Tier_Tournaments")
        for i in s_tier:
            tournaments.append(i)
        for i in a_tier:
            tournaments.append(i)
        for i in b_tier:
            tournaments.append(i)
        for tournament_db in tournaments_db:
            if tournament_db[0] not in tournaments_names and tournament_db[1] == self.discipline_id:
                await delete_tournament(tournament_db[0])
        return tournaments

    async def get_matches(self):
        games = []
        tournaments = []
        soup, __ = self.liquipedia.parse('Liquipedia:Matches')
        table = soup.find_all('table', class_='match')
        for match in table:
            game = {}
            game_time = match.find("span", class_="timer-object")
            game_tournament = match.find("div", class_="tournament-name")
            date_string, tz_string = game_time.get_text().rsplit(' ', 1)
            if (datetime.today() - parser.parse(date_string)) <= timedelta(days=2, hours=12):
                date = datetime.strptime(date_string, "%B %d, %Y - %H:%M")
                tz_needed = pytz.timezone("Asia/Yekaterinburg")
                if tz_string != "PET":
                    tz = pytz.timezone(self.timezones[tz_string][0])
                    date_res = date + timedelta(hours=self.tz_diff(date, tz, tz_needed))
                else:
                    tz = pytz.timezone(self.timezones['CDT'][0])
                    date_res = date + timedelta(hours=self.tz_diff(date, tz, tz_needed))
                game['time'] = date_res.strftime("%B %d, %Y - %H:%M")
                urls = game_tournament.find_all('a')
                for a in urls:
                    url = a.get('href').split('/')
                    if len(url) > 3:
                        if '/'.join(url[2:]) not in tournaments:
                            try:
                                tournaments.append('/'.join(url[2:]))
                                tournament_name, __ = self.liquipedia.parse('/'.join(url[2:]))
                                name = tournament_name.find('div', class_="infobox-header wiki-backgroundcolor-light")
                                game['tournament'] = name.get_text()[6:]
                                games.append(game)
                                await asyncio.sleep(30)
                            except Exception as e:
                                tournaments.append('/'.join(url[2:-1]))
                                tournament_name, __ = self.liquipedia.parse('/'.join(url[2:-1]))
                                name = tournament_name.find('div', class_="infobox-header wiki-backgroundcolor-light")
                                game['tournament'] = name.get_text()[6:]
                                games.append(game)
                                await asyncio.sleep(30)
                    else:
                        if url[2] not in tournaments:
                            tournaments.append(url[2])
                            tournament_name, __ = self.liquipedia.parse(url[2])
                            name = tournament_name.find('div', class_="infobox-header wiki-backgroundcolor-light")
                            game['tournament'] = name.get_text()[6:]
                            games.append(game)
                            await asyncio.sleep(30)
                print(game)
        return games