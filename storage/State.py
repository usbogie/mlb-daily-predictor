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

    def to_string(self):
        ret = "{} outs.".format(self.outs)
        if onFirst:
            ret = ret+" Runner on first."
        if onSecond:
            ret = ret+" Runner on second."
        if onThird:
            ret = ret+" Runner on third."
        return ret
