from dateutil import parser
import dateutil.parser
from DataBases.add_methods import add_tournament, add_games
from DataBases.delete_methods import delete_tournament
from DataBases.select_methods import select_tournaments, select_games
from LPRequest import LPRequest
from datetime import datetime
from dateutil import parser
import dateutil.tz as dtz
import pytz
import datetime as dt
import collections
from datetime import timedelta
import pandas as pd
import asyncio


class Base:
    def __init__(self, appname, game, discipline_id, game_name):
        self.appname = appname
        self.discipline_id = discipline_id
        self.liquipedia = LPRequest(appname, game=game)
        self.timezones = collections.defaultdict(list)
        self.game_name = game_name
        for name in pytz.all_timezones:
            timezone = dtz.gettz(name)
            try:
                now = dt.datetime.now(timezone)
            except ValueError:
                # dt.datetime.now(dtz.gettz('Pacific/Apia')) raises ValueError
                continue
            abbrev = now.strftime('%Z')
            self.timezones[abbrev].append(name)

    @staticmethod
    def tz_diff(date, tz1, tz2):
        date = pd.to_datetime(date)
        return (tz1.localize(date) -
                tz2.localize(date).astimezone(tz1)) \
            .seconds / 3600

    @staticmethod
    def is_today_before_date_range(date_range):
        try:
            start_date, end_date = date_range.split(' - ')
            if len(end_date.split(" ")) < 3:
                end_date = start_date.split(" ")[0] + " " + end_date
            end_date = parser.parse(end_date)
            today = datetime.today()
            if start_date == "May 10":
                print(end_date.year, today.year)
            return today <= end_date and today.year == end_date.year
        except dateutil.parser.ParserError:
            return True
        except ValueError:
            try:
                end_date = date_range
                if "??" in date_range:
                    return True
                end_date = parser.parse(end_date)
                today = datetime.today()
                return today <= end_date and today.year == end_date.year
            except dateutil.parser.ParserError:
                return True

    async def get_tournament(self):
        games = await select_games(self.game_name)
        if len(games) == 0:
            await add_games({"GameID": self.discipline_id, "Name": self.game_name})
        tournaments = []
        tournaments_names = []
        soup, __ = self.liquipedia.parse('Portal:Tournaments')
        tables = soup.find_all('div', class_="gridTable")
        tournaments_db = await select_tournaments()
        tournaments_db = [[i.Name, i.GameID] for i in tournaments_db]
        tournaments_db_names = []
        for i in tournaments_db:
            tournaments_db_names.append(i[0])
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
                tournament["tier"] = tournament_tier.get_text().split()[0]
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
                teams_on_tournament = tournament_teamscount.get_text()[0:3]
                teams_on_tournament = teams_on_tournament.replace(u"\xa0", u"")
                if len(teams_on_tournament) >= 2:
                    tournament["teams_count"] = teams_on_tournament
                else:
                    tournament["teams_count"] = "idk"
                tournament["place"] = tournament_place.get_text()
                print(tournament['tournament'], tournament["place"])
                if tournament['tournament'] not in tournaments_db_names:
                    await add_tournament({"Prize": str(tournament['prize']), "TeamsCount": tournament["teams_count"],
                                          "Tier": tournament["tier"], "GameID": self.discipline_id, "Name": tournament['tournament'], "Date": tournament["date"], "Location": tournament["place"]})
                tournaments.append(tournament)
        for tournament_db in tournaments_db:
            if tournament_db[0] not in tournaments_names and tournament_db[1] == self.discipline_id:
                await delete_tournament(tournament_db[0])
        return tournaments

    async def get_matches(self):
        games = []
        tournaments = []
        soup, __ = self.liquipedia.parse('Liquipedia:Upcoming_and_ongoing_matches')
        table = soup.find_all('table', class_='wikitable wikitable-striped infobox_matches_content')
        for match in table:
            game = {}
            game_time = match.find("span", class_="timer-object timer-object-countdown-only")
            game_tournament = match.find("div",
                                         style="text-align:right;overflow:hidden;text-overflow:ellipsis;max-width:170px;vertical-align:middle;white-space:nowrap;font-size:11px;height:16px;margin-top:3px;")
            date_string, tz_string = game_time.get_text().rsplit(' ', 1)
            if (datetime.today() - parser.parse(date_string)) <= timedelta(days=2, hours=12):
                date_upd = datetime.strptime(date_string, "%B %d, %Y - %H:%M")
                tz_needed = pytz.timezone("Asia/Yekaterinburg")
                if tz_string != "PET":
                    tz = pytz.timezone(self.timezones[tz_string][0])
                    date_res = date_upd + timedelta(hours=self.tz_diff(date_upd, tz, tz_needed))
                else:
                    tz = pytz.timezone(self.timezones['CDT'][0])
                    date_res = date_upd + timedelta(hours=self.tz_diff(date_upd, tz, tz_needed))
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
        return games
