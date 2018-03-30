from storage import Batter,Game,Pitcher,Scoreboard,State
import random

class MonteCarlo(object):
    scoreboard = None
    game = None
    away_lineup = []
    home_lineup = []
    away_pitchers = []
    home_pitchers = []
    game_completed = None

    home_batter = 0
    away_batter = 0

    home_wins = 0
    away_wins = 0
    home_win_prob = 0.0
    away_win_prob = 0.0
    avg_home_total = 0.0
    avg_away_total = 0.0
    avg_total = 0.0

    histo_bins = 50;
    home_histo = []
    away_histo = []
    comb_histo = []
    number_of_sims = 1
    num_innings = 9

    def __init__(self, game, away_lineup, home_lineup, away_pitchers, home_pitchers):
        self.game = game
        self.away_lineup = away_lineup
        self.home_lineup = home_lineup
        self.away_pitchers = away_pitchers
        self.home_pitchers = home_pitchers

        self.home_histo = [0]*50
        self.away_histo = [0]*50
        self.comb_histo = [0]*50

    def sim_one_game(self):
        self.scoreboard = Scoreboard()
        self.game_completed = False
        self.home_batter = 0
        self.away_batter = 0

        while not game_completed:
            self.scoreboard.add_frame()
            self.play_frame()

            if (len(self.scoreboard.frames) >= 18 and
                len(self.scoreboard.frames)%2==0) and
                self.scoreboard.get_away_runs() != self.scoreboard.get_home_runs()):
                # 9+ full innings completed, no tie, end game
                self.game_completed = True

    def sim_games(self):
        if len(self.away_lineup) < 9 or len(self.home_lineup) < 9 or
            len(self.away_pitchers) == 0 or len(self.home_pitchers) == 0:
            #something wrong, exit
            return

        for i in range(this.number_of_sims):
            self.scoreboard = self.sim_one_game()
            int total_runs = self.scoreboard.get_away_runs() + self.scoreboard.get_home_runs()
            self.comb_histo[total_runs] = self.comb_histo[total_runs] + 1
            self.away_histo[self.scoreboard.get_away_runs()] = self.away_histo[self.scoreboard.get_away_runs()] + 1
            self.home_histo[self.scoreboard.get_home_runs()] = self.home_histo[self.scoreboard.get_home_runs()] + 1

            if self.scoreboard.home_win():
                self.home_wins = self.home_wins + 1
            else:
                self.away_wins = self.away_wins + 1

        self.home_win_prob = self.home_wins / float(self.number_of_sims)
        self.away_win_prob = self.away_wins / float(self.number_of_sims)
        self.avg_away_total = [self.away_histo[x]*x for x in self.away_histo]/float(self.number_of_sims)
        self.avg_home_total = [self.home_histo[x]*x for x in self.home_histo]/float(self.number_of_sims)
        self.avg_total = [self.comb_histo[x]*x for x in self.comb_histo]/float(self.number_of_sims)

    def play_frame(self):
        state = State()
        batting_order = []
        batting_num = 0
        pitcher = None
        away_batting = len(self.scoreboard.frames)%2==0

        if away_batting:
            batting_num = self.away_batter
            batting_order = self.away_lineup
            pitcher = self.home_pitchers[0]
        else:
            batting_num = self.home_batter
            batting_order = self.home_lineup
            pitcher = self.away_pitchers[0]

        while state.outs < 3:
            if not away_batting and len(self.scoreboard.frames) > 17 and
                    self.scoreboard.get_away_runs() < self.scoreboard.get_home_runs():
                self.game_completed = True
                break

            state = self.sim_atbat(batting_order[batting_num], pitcher, state)

            batting_num = batting_num + 1
            if batting_num >= len(batting_order):
                batting_num = 0

        if away_batting:
            self.away_batter = batting_num
        else:
            self.home_batter = batting_num

    def sim_atbat(self, batter, pitcher, state):
        draw = float(random.random())
        #TODO a lot. Need to develop a way to determine SO/NON-SO-OUT/walk/1b/2b/3b/hr/HPB(necessary?)
        #And then scale it all between [0,1). THEN, look at the estimator.py file and use That
        #to create baserunning logic. NOT HARD just a lot of work and attention to detail
        #http://www.insidethebook.com/ee/index.php/site/comments/the_odds_ratio_method/ for hitter/pitcher matchups
