from storage.Scoreboard import Scoreboard
from storage.Game import Game
from storage.State import State

from math import floor
import random
import os

class MonteCarlo(object):
    scoreboard = None
    game = None
    away_lineup = []
    home_lineup = []
    away_pitchers = []
    home_pitchers = []
    league_avgs = {}
    game_completed = None
    park_factors = {}

    home_batter = 0
    away_batter = 0
    home_pitcher = 0
    away_pitcher = 0

    home_wins = 0
    away_wins = 0
    home_win_prob = 0.0
    away_win_prob = 0.0
    avg_home_total = 0.0
    avg_away_total = 0.0
    avg_total = 0.0

    f5_home_wins = 0
    f5_away_wins = 0
    f5_ties = 0
    f5_home_win_prob = 0.0
    f5_away_win_prob = 0.0
    f5_home_win_no_tie_prob = 0.0
    f5_away_win_no_tie_prob = 0.0
    f5_tie_prob = 0.0
    f5_avg_total = 0.0

    home_rl_fav_wins = 0
    away_rl_fav_wins = 0
    home_rl_dog_wins = 0
    away_rl_dog_wins = 0

    scored_in_first = False
    scores_in_first = 0
    away_strikeouts = 0
    home_strikeouts = 0

    home_histo = []
    away_histo = []
    comb_histo = []
    f5_comb_histo = []
    number_of_sims = 10000

    def __init__(self, game, away_lineup, home_lineup, away_pitchers, home_pitchers, league_avgs, park_factors):
        self.game = game
        self.away_lineup = away_lineup
        self.home_lineup = home_lineup
        self.away_pitchers = away_pitchers
        self.home_pitchers = home_pitchers
        self.league_avgs = league_avgs
        self.park_factors = park_factors

        self.home_histo = [0]*50
        self.away_histo = [0]*50
        self.comb_histo = [0]*50
        self.f5_comb_histo = [0]*50


    def sim_one_game(self):
        self.scoreboard = Scoreboard()
        self.game_completed = False
        self.home_batter = 0
        self.away_batter = 0
        self.home_pitcher = 0
        self.away_pitcher = 0
        self.scored_in_first = False

        while not self.game_completed:
            self.scoreboard.add_frame()
            self.play_frame()

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

            if (len(self.scoreboard.frames) >= 18 and \
                len(self.scoreboard.frames)%2 == 0 and \
                self.scoreboard.get_away_runs() != self.scoreboard.get_home_runs()):
                # 9+ full innings completed, no tie, end game
                #print('Final score:', self.scoreboard.get_away_runs(), 'to', self.scoreboard.get_home_runs())
                self.game_completed = True

    def sim_games(self):
        if len(self.away_lineup) < 9 or len(self.home_lineup) < 9 or \
            len(self.away_pitchers) == 0 or len(self.home_pitchers) == 0:
            #something wrong, exit
            print(len(self.away_lineup),len(self.home_lineup),len(self.away_pitchers),len(self.home_pitchers))
            print([x['PA'] for x in self.home_lineup])
            print("something wrong")
            return

        for i in range(self.number_of_sims):
            self.sim_one_game()
            total_runs = self.scoreboard.get_away_runs() + self.scoreboard.get_home_runs()
            self.comb_histo[total_runs] = self.comb_histo[total_runs] + 1
            self.away_histo[self.scoreboard.get_away_runs()] = self.away_histo[self.scoreboard.get_away_runs()] + 1
            self.home_histo[self.scoreboard.get_home_runs()] = self.home_histo[self.scoreboard.get_home_runs()] + 1

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

        self.home_win_prob = self.home_wins / float(self.number_of_sims)
        self.away_win_prob = self.away_wins / float(self.number_of_sims)
        self.avg_away_total = sum([self.away_histo[x]*x for x in range(50)])/float(self.number_of_sims)
        self.avg_home_total = sum([self.home_histo[x]*x for x in range(50)])/float(self.number_of_sims)
        self.avg_total = sum([self.comb_histo[x]*x for x in range(50)])/float(self.number_of_sims)

        self.f5_home_win_prob = self.f5_home_wins / float(self.number_of_sims - self.f5_ties)
        self.f5_away_win_prob = self.f5_away_wins / float(self.number_of_sims - self.f5_ties)
        self.f5_home_win_no_tie_prob = self.f5_home_wins / float(self.number_of_sims)
        self.f5_away_win_no_tie_prob = self.f5_away_wins / float(self.number_of_sims)
        self.f5_tie_prob = self.f5_ties / float(self.number_of_sims)
        self.f5_avg_total = sum([self.f5_comb_histo[x]*x for x in range(50)])/float(self.number_of_sims)


    def play_frame(self):
        state = State()
        batting_order = []
        batting_num = 0
        pitcher = None
        away_batting = (self.scoreboard.current_frame % 2) ==  0

        if away_batting:
            batting_num = self.away_batter
            batting_order = self.away_lineup
            pitcher = self.determine_pitcher(True)
        else:
            batting_num = self.home_batter
            batting_order = self.home_lineup
            pitcher = self.determine_pitcher(False)

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
        rand = random.random()
        outcome_dict = self.get_outcome_distribution(batter,pitcher)
        event = None
        for i in range(len(list(outcome_dict))):
            if rand < sum(list(outcome_dict.values())[:i+1]):
                event = list(outcome_dict.keys())[i]
                break

        #print(event)
        if event == '1B':
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
        if event == '2B':
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
        if event == '3B':
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
        if event == 'HR':
            if state.onThird:
                self.increment_runs()
            if state.onSecond:
                self.increment_runs()
            if state.onFirst:
                self.increment_runs()
            self.increment_runs()
            state.clear_bases()
        if event == 'K':
            if pitcher == self.away_pitchers[0]:
                self.away_strikeouts = self.away_strikeouts + 1
            elif pitcher == self.home_pitchers[0]:
                self.home_strikeouts = self.home_strikeouts + 1
            state.outs = state.outs + 1
        if event == 'BB' or event == 'HBP':
            if state.onFirst and state.onSecond and state.onThird:
                self.increment_runs()
            elif state.onFirst and state.onSecond:
                state.onThird = True
            elif state.onFirst:
                state.onSecond = True
            state.onFirst = True
        if event == 'OutNonK':
            state.outs = state.outs + 1
            if state.onThird and state.outs < 3:
                if state.determine_extra_base(event, '3'):
                    self.increment_runs()
                    state.onThird = False
            if state.onSecond and state.outs < 3:
                if not state.onThird and state.determine_extra_base(event, '2'):
                    state.onThird = True
                    state.onSecond = False
            if state.onFirst and state.outs < 3:
                if not state.onSecond and state.determine_extra_base(event, '1'):
                    state.onSecond = True
                    state.onFirst = False
        #print(state.to_string())
        return state

    def increment_runs(self):
        if self.scoreboard.current_frame < 2 and not self.scored_in_first:
            self.scored_in_first = True
            self.scores_in_first = self.scores_in_first + 1
        self.scoreboard.inc_runs()

    def get_outcome_distribution(self, batter, pitcher):
        park_factors = self.park_factors[0]
        pitcher_hand = pitcher['Throws']
        batter_split = batter['v'+pitcher_hand]
        batter_hand = batter_split['bats']
        batter_hand = batter_hand if batter_hand != 'B' else ('R' if pitcher_hand == 'L' else 'L')
        outcomes_w_factor = ["1B","2B","3B","HR"]
        outcomes_wo_factor = ["K","HBP","BB"]
        outcomes = outcomes_w_factor +outcomes_wo_factor
        bat_outcomes_w_factor = {outcome: batter_split[outcome]*(park_factors[outcome+batter_hand]/100)/batter_split["PA"] for outcome in outcomes_w_factor}
        bat_outcomes_wo_factor = {outcome: batter_split[outcome]/batter_split["PA"] for outcome in outcomes_wo_factor}
        bat_outcomes = {**bat_outcomes_w_factor,**bat_outcomes_wo_factor}
        bat_outcomes["OutNonK"] = 1-sum(bat_outcomes.values())
        p_outcomes = ["K","BB","HBP","1b","2b","3b","HR"]
        pitch_outcomes = {outcome: pitcher[outcome]/pitcher["TBF"] for outcome in p_outcomes}
        pitch_outcomes["1B"] = pitch_outcomes.pop("1b")
        pitch_outcomes["2B"] = pitch_outcomes.pop("2b")
        pitch_outcomes["3B"] = pitch_outcomes.pop("3b")
        pitch_outcomes["OutNonK"] = 1-sum(pitch_outcomes.values())
        league_outcomes = dict(self.league_avgs)
        league_outcomes["OutNonK"] = 1-sum(league_outcomes.values())
        outcomes.append("OutNonK")
        denom = {outcome: bat_outcomes[outcome]*pitch_outcomes[outcome]/league_outcomes[outcome]
                 for outcome in outcomes}
        normalizer = sum(denom.values())
        outcome_dict = {k: v/normalizer for k, v in denom.items()}
        return outcome_dict

    def determine_pitcher(self, home):
        #print(self.scoreboard.get_away_runs(),'to',self.scoreboard.get_home_runs(), 'frame', len(self.scoreboard.frames))
        pitchers = self.home_pitchers if home else self.away_pitchers
        pitcher_num = self.home_pitcher if home else self.away_pitcher
        pitcher = pitchers[pitcher_num]
        if pitcher_num == 0:
            # determine if starter should be pulled
            pull_starter = False
            try:
                avg_start_length = pitcher['start_IP'] / pitcher['GS']
            except:
                avg_start_length = 4.5
            cur_inning = len(self.scoreboard.frames)//2 + 1
            rand = random.random()
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

        # bring in closer?
        home_margin = self.scoreboard.get_home_runs() - self.scoreboard.get_away_runs()
        if len(self.scoreboard.frames)//2 + 1 == 9 and \
                ((home and home_margin < 5 and home_margin > -1) or \
                (not home and home_margin > -5)):
            #print("Closer situation")
            team_closers = [x for x in pitchers if x['SV'] > 1.0]
            total = sum([x['SV'] for x in team_closers])
            rand = random.random()
            for i in range(len(team_closers)):
                if rand < sum([x['SV'] for x in team_closers[:i+1]])/total:
                    #print(team_closers[i]['lastname'], 'is the closer')
                    return team_closers[i]
                # print(team_closers[i]['lastname'], 'is not the closer')

        #randomly select reliever based on IP
        total_relief_innings = sum([x['relief_IP'] for x in pitchers])
        relief_pitchers = [x for x in pitchers if x['relief_IP'] > 0]
        rand = random.random()
        for i in range(0,len(relief_pitchers)):
            if rand < sum([x['relief_IP'] for x in relief_pitchers[:i+1]])/total_relief_innings:
                #print(relief_pitchers[i]['lastname'], 'is the new reliever')
                return relief_pitchers[i]
            # print(relief_pitchers[i]['lastname'], 'is not the new reliever')
        print("SHOULD NEVER GET HERE")
        sys.exit()
