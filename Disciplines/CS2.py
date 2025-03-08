from datetime import datetime
from dateutil import parser
import pytz
from datetime import timedelta
import pandas as pd
import asyncio
from Disciplines.BaseDiscipline import Base


def tz_diff(date, tz1, tz2):
    date = pd.to_datetime(date)
    return (tz1.localize(date) -
            tz2.localize(date).astimezone(tz1))\
        .seconds/3600


class CS(Base):
    def __init__(self, appname, game, discipline_id, game_name):
        super().__init__(appname, game, discipline_id, game_name)

    async def get_matches(self):
        games = []
        tournaments = []
        soup, __ = self.liquipedia.parse('Liquipedia:Matches')
        table = soup.find_all('table', class_='wikitable wikitable-striped infobox_matches_content')
        for match in table:
            game = {}
            game_time = match.find("span", class_="timer-object timer-object-countdown-only")
            game_tournament = match.find("div", class_="text-nowrap")
            date_string, tz_string = game_time.get_text().rsplit(' ', 1)
            if (datetime.today() - parser.parse(date_string)) <= timedelta(days=2, hours=12):
                date = datetime.strptime(date_string, "%B %d, %Y - %H:%M")
                tz_needed = pytz.timezone("Asia/Yekaterinburg")
                if tz_string != "PET":
                    tz = pytz.timezone(self.timezones[tz_string][0])
                    date_res = date + timedelta(hours=tz_diff(date, tz, tz_needed))
                else:
                    tz = pytz.timezone(self.timezones['CDT'][0])
                    date_res = date + timedelta(hours=tz_diff(date, tz, tz_needed))
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
