from Disciplines.BaseDiscipline import Base


class Apex(Base):
    def __init__(self, appname, game, discipline_id, game_name):
        super().__init__(appname, game, discipline_id, game_name)
