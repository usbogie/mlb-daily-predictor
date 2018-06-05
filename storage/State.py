class State(object):
    outs = 0
    onFirst = False
    onSecond = False
    onThird = False

    def end_inning(self):
        self.outs = 0
        self.clear_bases()

    def clear_bases(self):
        self.onFirst = False
        self.onSecond = False
        self.onThird = False

    def determine_extra_base(self, event, base):
        import random
        rand = random.random()
        if event == 'single':
            if base == '1':
                if rand < 0.27:
                    return True
                else:
                    return False
            if base == '2':
                if (self.outs == 0 and rand < 0.5) or \
                    (self.outs == 1 and rand < 0.65) or \
                    (self.outs == 2 and rand < 0.75):
                    return True
                else:
                    return False
        elif event == 'double':
            if (self.outs == 0 and rand < 0.40) or \
                (self.outs == 1 and rand < 0.50) or \
                (self.outs == 2 and rand < 0.60):
                return True
            else:
                return False
        elif event == 'OutNonK':
            if base == '1':
                if self.outs < 3 and rand < 0.25:
                    return True
                else:
                    return False
            if base == '2':
                if self.outs < 3 and rand < 0.50:
                    return True
                else:
                    return False
            if base == '3':
                if self.outs < 3 and rand < 0.75:
                    return True
                else:
                    return False
        print("Never should be able to get here. Logic is wrong")
        return False

    def to_string(self):
        ret = "{} outs.".format(self.outs)
        if self.onFirst:
            ret = ret+" Runner on first."
        if self.onSecond:
            ret = ret+" Runner on second."
        if self.onThird:
            ret = ret+" Runner on third."
        return ret
