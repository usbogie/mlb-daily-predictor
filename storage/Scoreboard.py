class ScoreBoard(object):
    frames = []
    away_hits = 0
    home_hits = 0
    current_frame = -1

    def add_frame(self):
        self.frames.append(0)
        self.current_frame += 1

    def inc_runs(self):
        self.frames[self.current_frame] = self.frames[self.current_frame] + 1

    def inc_hits(self):
        if self.current_frame%2 == 0:
            self.away_hits += 1
        else:
            self.home_hits += 1

    def get_away_runs(self):
        return sum(self.frames[::2])

    def get_home_runs(self):
        return sum(self.frames[1::2])

    def home_win(self):
        if self.get_away_runs() > self.get_home_runs():
            return False
        return True
