class Scoreboard(object):
    frames = []
    current_frame = -1

    def __init__(self):
        self.frames = []
        self.current_frame = -1

    def add_frame(self):
        self.frames.append(0)
        self.current_frame += 1

    def inc_runs(self):
        self.frames[self.current_frame] = self.frames[self.current_frame] + 1

    def get_away_runs(self):
        return sum(self.frames[::2])

    def get_home_runs(self):
        return sum(self.frames[1::2])

    def home_win(self):
        return self.get_away_runs() < self.get_home_runs()
