class Game(object):
    date = ""
    time = ""
    game_id = ""
    away_id = ""
    away_name = ""
    home_id = ""
    home_name = ""
    park_id = ""
    park_name = ""

    def __init__(self,date,time,game_id,away_id,away_name,home_id,home_name,park_id,park_name):
        self.date = date
        self.time = time
        self.game_id = game_id
        self.away_id = away_id
        self.away_name = away_name
        self.home_id = home_id
        self.home_name = home_name
        self.park_id = park_id
        self.park_name = park_name
