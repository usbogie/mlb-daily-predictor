from storage.Scoreboard import Scoreboard
from storage.Game import Game
from storage.State import State

from math import floor
import random
import os

class MonteCarlo(object):
    away_lineup = []
    home_lineup = []
    away_pitchers = []
    home_pitchers = []
    matchups = []

    home_batter = 0
    away_batter = 0
    home_pitcher = 0
    away_pitcher = 0

    home_wins = 0
    away_wins = 0
    home_rl_fav_wins = 0
    away_rl_fav_wins = 0
    home_rl_dog_wins = 0
    away_rl_dog_wins = 0

    f5_home_wins = 0
    f5_away_wins = 0
    f5_ties = 0
    f5_home_rl_fav_wins = 0
    f5_away_rl_fav_wins = 0
    f5_home_rl_dog_wins = 0
    f5_away_rl_dog_wins = 0

    scored_in_first = False
    scores_in_first = 0

    comb_histo = []
    f5_comb_histo = []
    number_of_sims = 10000

    def __init__(self, game, away_lineup, home_lineup, away_pitchers, home_pitchers, matchups):
        self.game = game
        self.away_lineup = away_lineup
        self.home_lineup = home_lineup
        self.away_pitchers = away_pitchers
        self.home_pitchers = home_pitchers
        self.matchups = matchups


        self.comb_histo = [0]*75
        self.f5_comb_histo = [0]*75

    def sim_results(self):
        return dict(
            home_win_prob = self.home_wins / self.number_of_sims * 1.08,
            home_dog_rl_prob = self.home_rl_dog_wins / self.number_of_sims * 1.08,
            home_fav_rl_prob = self.home_rl_fav_wins / self.number_of_sims * 1.08,

            f5_home_win_prob = self.f5_home_wins / (self.number_of_sims - self.f5_ties) * 1.08,
            f5_away_win_prob = self.f5_away_wins / (self.number_of_sims - self.f5_ties) / 1.08,
            f5_home_fav_win_prob = self.f5_home_wins / self.number_of_sims * 1.08,
            f5_home_dog_win_prob = (self.f5_home_wins + self.f5_ties) / self.number_of_sims * 1.08,

            score_in_first = self.scores_in_first / self.number_of_sims,
        )

    def sim_games(self,test=False):
        if len(self.away_lineup) < 9 or len(self.home_lineup) < 9 or \
            len(self.away_pitchers) == 0 or len(self.home_pitchers) == 0:
            #something wrong, exit
            print(len(self.away_lineup),len(self.home_lineup),len(self.away_pitchers),len(self.home_pitchers))
            print([x['PA'] for x in self.home_lineup])
            print("something wrong")
            return

        for i in range(self.number_of_sims):
            self.sim_one_game(test)
            total_runs = self.scoreboard.get_away_runs() + self.scoreboard.get_home_runs()
            self.comb_histo[total_runs] = self.comb_histo[total_runs] + 1

            if self.scoreboard.home_win():
                self.home_wins = self.home_wins + 1
            else:
                self.away_wins = self.away_wins + 1

            if self.scoreboard.get_home_runs() > self.scoreboard.get_away_runs() + 1:
                self.home_rl_fav_wins = self.home_rl_fav_wins + 1
            else:
                self.away_rl_dog_wins = self.away_rl_dog_wins + 1
            if self.scoreboard.get_home_runs() + 1 < self.scoreboard.get_away_runs():
                self.away_rl_fav_wins = self.away_rl_fav_wins + 1
            else:
                self.home_rl_dog_wins = self.home_rl_dog_wins + 1

    def sim_one_game(self,test):
        self.scoreboard = Scoreboard()
        self.home_batter = 0
        self.away_batter = 0
        self.home_pitcher = 0
        self.away_pitcher = 0
        self.scored_in_first = False

        while True:
            self.scoreboard.add_frame()
            self.play_frame(test)

            if len(self.scoreboard.frames) == 10:
                #lock in f5 attrs
                if self.scoreboard.get_home_runs() > self.scoreboard.get_away_runs():
                    self.f5_home_wins = self.f5_home_wins + 1
                elif self.scoreboard.get_home_runs() == self.scoreboard.get_away_runs():
                    self.f5_ties = self.f5_ties + 1
                else:
                    self.f5_away_wins = self.f5_away_wins + 1
                f5_total_runs = self.scoreboard.get_away_runs() + self.scoreboard.get_home_runs()
                self.f5_comb_histo[f5_total_runs] = self.f5_comb_histo[f5_total_runs] + 1

            if (len(self.scoreboard.frames) >= 18 and len(self.scoreboard.frames)%2 == 0 and \
                    self.scoreboard.get_away_runs() != self.scoreboard.get_home_runs()):
                # 9+ full innings completed, no tie, end game
                #print('Final score:', self.scoreboard.get_away_runs(), 'to', self.scoreboard.get_home_runs())
                break

    def play_frame(self,test):
        state = State()
        batting_order = []
        batting_num = 0
        pitcher = None
        away_batting = (self.scoreboard.current_frame % 2) ==  0

        if away_batting:
            batting_num = self.away_batter
            batting_order = self.away_lineup
            pitcher = self.determine_pitcher(True,test)
        else:
            batting_num = self.home_batter
            batting_order = self.home_lineup
            pitcher = self.determine_pitcher(False,test)

        while state.outs < 3:
            if not away_batting and len(self.scoreboard.frames) > 17 and \
                self.scoreboard.get_away_runs() < self.scoreboard.get_home_runs():
                # if home team is up in the bottom of the ninth or beyond, end the game
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
        # possible outcomes: K,BB,HBP,1B,2B,3B,HR,OutNonK
        outcomes = self.matchups[(pitcher['mlb_id'],batter['mlb_id'])]
        event = None
        rand = random.random()
        for (key, val) in outcomes:
            if rand < val:
                event = key
                break

        #print(event)
        if event == 'OutNonK':
            state.outs = state.outs + 1
            if state.outs < 3:
                if state.onThird:
                    if state.determine_extra_base(event, '3'):
                        self.increment_runs()
                        state.onThird = False
                if state.onSecond:
                    if not state.onThird and state.determine_extra_base(event, '2'):
                        state.onThird = True
                        state.onSecond = False
                if state.onFirst:
                    if not state.onSecond and state.determine_extra_base(event, '1'):
                        state.onSecond = True
                        state.onFirst = False
        if event == 'k':
            state.outs = state.outs + 1
        if event == 'bb' or event == 'hpb':
            if state.onFirst:
                if state.onSecond:
                    if state.onThird:
                        self.increment_runs()
                    state.onThird = True
                state.onSecond = True
            state.onFirst = True
        if event == 'single':
            if state.onThird:
                self.increment_runs()
                state.onThird = False
            second_takes_extra = False
            if state.onSecond:
                second_takes_extra = state.determine_extra_base(event, '2')
                if second_takes_extra:
                    self.increment_runs()
                else:
                    state.onThird = True
                state.onSecond = False
            if state.onFirst:
                first_takes_extra = False
                if second_takes_extra:
                    first_takes_extra = state.determine_extra_base(event, '1')
                if first_takes_extra:
                    state.onThird = True
                else:
                    state.onSecond = True
                state.onFirst = False
            state.onFirst = True
        if event == 'double':
            if state.onThird:
                self.increment_runs()
                state.onThird = False
            if state.onSecond:
                self.increment_runs()
                state.onSecond = False
            if state.onFirst:
                first_takes_extra = state.determine_extra_base(event, '1')
                if first_takes_extra:
                    self.increment_runs()
                else:
                    state.onThird = True
                state.onFirst = False
            state.onSecond = True
        if event == 'hr':
            if state.onThird:
                self.increment_runs()
            if state.onSecond:
                self.increment_runs()
            if state.onFirst:
                self.increment_runs()
            self.increment_runs()
            state.clear_bases()
        if event == 'triple':
            if state.onThird:
                self.increment_runs()
                state.onThird = False
            if state.onSecond:
                self.increment_runs()
                state.onSecond = False
            if state.onFirst:
                self.increment_runs()
                state.onFirst = False
            state.onThird = True
        #print(state.to_string())
        return state

    def increment_runs(self):
        if self.scoreboard.current_frame < 2 and not self.scored_in_first:
            self.scored_in_first = True
            self.scores_in_first = self.scores_in_first + 1
        self.scoreboard.inc_runs()

    def is_opener(self, pitcher):
        opener_ids = {'Liam Hendriks': 521230, 'Brandon Woodruff': 605540, 'Gio Gonzalez': 461829}
        if pitcher['mlb_id'] in list(opener_ids.values()):
            return True
        return False

    def determine_pitcher(self, home, test):
        #print(self.scoreboard.get_away_runs(),'to',self.scoreboard.get_home_runs(), 'frame', len(self.scoreboard.frames))
        pitchers = self.home_pitchers if home else self.away_pitchers
        pitcher_num = self.home_pitcher if home else self.away_pitcher
        pitcher = pitchers[pitcher_num]
        if pitcher_num == 0:
            # determine if starter should be pulled
            pull_starter = False
            cur_inning = len(self.scoreboard.frames)//2 + 1
            rand = random.random()
            if self.is_opener(pitcher):
                if not ((cur_inning == 2 and rand < .2) or \
                    (cur_inning == 3 and rand < .4) or \
                    (cur_inning == 3 and rand < .8) or \
                    (cur_inning == 4 and rand < 1.00)):
                    return pitcher
            else:
                if not pitcher['GS'] == 0.0:
                    avg_start_length = pitcher['start_IP'] / pitcher['GS']
                else:
                    avg_start_length = 4.5
                if not ((cur_inning == floor(avg_start_length)-1 and rand < .15) or \
                    (cur_inning == floor(avg_start_length)+0 and rand < .25) or \
                    (cur_inning == floor(avg_start_length)+1 and rand < .50) or \
                    (cur_inning == floor(avg_start_length)+2 and rand < .70) or \
                    (cur_inning == floor(avg_start_length)+3 and rand < .90) or \
                    (cur_inning == floor(avg_start_length)+4 and rand < .99) or \
                    (cur_inning == floor(avg_start_length)+5 and rand < 1.00)):
                    return pitcher
            #print("pulling starter", pitcher['lastname'],'before',cur_inning,'inning')
            if home:
                self.home_pitcher = 1
            else:
                self.away_pitcher = 1

        home_margin = self.scoreboard.get_home_runs() - self.scoreboard.get_away_runs()
        if len(self.scoreboard.frames)//2 + 1 in [9] and \
                ((home and home_margin < 5 and home_margin > -5) or \
                (not home and home_margin > -5)):
            #print("Closer situation")
            #print(team_closers[i]['lastname'], 'is the closer')
            if not test:
                return pitchers[-1]
            else:
                r = random.randint(1,len(pitchers)-1)
                return pitchers[r]

        #randomly select reliever based on usage
        relief_pitchers = [x for x in pitchers[1:-1]]
        rand = random.random()
        for i in range(len(relief_pitchers)):
            if rand < sum([x['usage'] for x in relief_pitchers[:i+1]]):
                # print(relief_pitchers[i]['fullname'], 'is the new reliever')
                return relief_pitchers[i]
        # print(relief_pitchers[i]['fullname'], 'is the new reliever')
        return random.choice(relief_pitchers)
