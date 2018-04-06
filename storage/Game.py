class Game(object):
    date = ""
    time = ""
    away_name = ""
    home_name = ""

    def __init__(self,date,time,away_name,home_name):
        self.date = date
        self.time = time
        self.away_name = away_name
        self.home_name = home_name
