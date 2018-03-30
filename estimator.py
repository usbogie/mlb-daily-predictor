import numpy

recRuns = []
recInnings = []
recIter = []
recRetVal = []

event1B_state1B_0 = event1B_state1B_1 = event1B_state1B_2 = 0.25

event1B_state2B_0 = 0.3
event1B_state2B_1 = 0.5
event1B_state2B_2 = 0.75

event2B_state1B_0 = 0.15
event2B_state1B_1 = 0.25
event2B_state1B_2 = 0.5

eventOUT_state1B_0 = eventOUT_state1B_1 = 0.05
eventOUT_state1B_2 = 0.0

eventOUT_state2B_0 = eventOUT_state2B_1 = 0.25
eventOUT_state2B_2 = 0.0

eventOUT_state3B_0 = eventOUT_state3B_1 = 0.5
eventOUT_state3B_2 = 0.0

stats = {
	"valAB": 37,
	"valH": 10,
	"val2B": 2,
	"val3B": 0,
	"valHR": 2,
	"valBB": 4,
	"valSO": 7,
}

p = numpy.empty(150, dtype=int)
recDepth = 0

recScore = numpy.empty(150, dtype=int)
recAll = numpy.empty(150, dtype=int)
ways = numpy.empty(150, dtype=int)

recOuts = []
recBR = []
recPerms   = []

# var exact_cache = new Array(1000);

# rfs - this implements the run frequency variables (RF_BBB_O) as a multi-dimensional array
# making them more flexible for processing in loops, etc.
# example : frequency of scoring at least 1 run from runner on 1st, 2 outs
# RF_1xx_2 --> rfs[1][0][0][2]

rfs = [[[[None]*3,[None]*3],
		[[None]*3,[None]*3]],
	   [[[None]*3,[None]*3],
		[[None]*3,[None]*3]]]



min_cache = [[[[numpy.empty(500, dtype=int),numpy.empty(500, dtype=int),numpy.empty(500, dtype=int)],
			   [numpy.empty(500, dtype=int),numpy.empty(500, dtype=int),numpy.empty(500, dtype=int)]],
			  [[numpy.empty(500, dtype=int),numpy.empty(500, dtype=int),numpy.empty(500, dtype=int)],
			   [numpy.empty(500, dtype=int),numpy.empty(500, dtype=int),numpy.empty(500, dtype=int)]]],
			 [[[numpy.empty(500, dtype=int),numpy.empty(500, dtype=int),numpy.empty(500, dtype=int)],
			   [numpy.empty(500, dtype=int),numpy.empty(500, dtype=int),numpy.empty(500, dtype=int)]],
			  [[numpy.empty(500, dtype=int),numpy.empty(500, dtype=int),numpy.empty(500, dtype=int)],
			   [numpy.empty(500, dtype=int),numpy.empty(500, dtype=int),numpy.empty(500, dtype=int)]]]]

min_add_count = 0
min_use_count = 0

exact_cache = [[[[numpy.empty(500, dtype=int),numpy.empty(500, dtype=int),numpy.empty(500, dtype=int)],
				 [numpy.empty(500, dtype=int),numpy.empty(500, dtype=int),numpy.empty(500, dtype=int)]],
				[[numpy.empty(500, dtype=int),numpy.empty(500, dtype=int),numpy.empty(500, dtype=int)],
				 [numpy.empty(500, dtype=int),numpy.empty(500, dtype=int),numpy.empty(500, dtype=int)]]],
			   [[[numpy.empty(500, dtype=int),numpy.empty(500, dtype=int),numpy.empty(500, dtype=int)],
				 [numpy.empty(500, dtype=int),numpy.empty(500, dtype=int),numpy.empty(500, dtype=int)]],
				[[numpy.empty(500, dtype=int),numpy.empty(500, dtype=int),numpy.empty(500, dtype=int)],
				 [numpy.empty(500, dtype=int),numpy.empty(500, dtype=int),numpy.empty(500, dtype=int)]]]]

exact_add_count = 0
exact_use_count = 0

# woolner_cache - emulates a multi-dimensional array
# used to cache the results of calculations performed using the pWoolnerStack function
# eliminates redundant calculations and enhamces performance

woolner_cache = [numpy.empty(500, dtype=int),
				 numpy.empty(500, dtype=int),
				 numpy.empty(500, dtype=int),
				 numpy.empty(500, dtype=int),
				 numpy.empty(500, dtype=int),
				 numpy.empty(500, dtype=int),
				 numpy.empty(500, dtype=int),
				 numpy.empty(500, dtype=int),
				 numpy.empty(500, dtype=int),
				 numpy.empty(500, dtype=int)]

# ob_perms_cache - used to cache the results of calculations using the ob_permutations function
# eliminates redundant calculations and enhamces performance

ob_perm_cache =[numpy.empty(500, dtype=int), numpy.empty(500, dtype=int), numpy.empty(500, dtype=int),
				numpy.empty(500, dtype=int), numpy.empty(500, dtype=int), numpy.empty(500, dtype=int),
				numpy.empty(500, dtype=int), numpy.empty(500, dtype=int), numpy.empty(500, dtype=int),
				numpy.empty(500, dtype=int), numpy.empty(500, dtype=int), numpy.empty(500, dtype=int)]

ob_add_count = 0
ob_use_count = 0

# initialize frequencies per PA for all variables
frq = {
	"freqOBP": 0,
	"freqBB": 0,
	"freq1B": 0,
	"freq2B": 0,
	"freq3B": 0,
	"freqHR": 0,
	"freqSO": 0,
	"freqOUT": 0,
	"freqH": 0,
	"freqPA": 0,
	"rateNonK_OUT": 0
}

# a function to handle exponentiation - e.g. 2^3 = myEXP(2,3)
def myEXP(parm_base,parm_exp):
	return (parm_base**parm_exp)

#function to prepopulate the values of the woolner_cache and ways_cache
def prepopulate_caches():
	print("about to prepopulate the caches")

	# prepopulate the woolner_cache array
	for i in range(1,10):
		for r in range(500):
			#alertString = "["+i+"]["+r+"]"
			#print(alertString)
			woolner_cache[i][r] = -1

	# prepopulate the ob_perm_cache
	for o in range(3):
		for r in range(500):
			ob_perm_cache[o][r] = -1

	# prepopulate the exact_cache
	for r1 in range(2):
		for r2 in range(2):
			for r3 in range(2):
				for o in range(3):
					for r in range(500):
						exact_cache[r1][r2][r3][o][r] = -1

	#prepopulate min_cache
	for r1 in range(2):
		for r2 in range(2):
			for r3 in range(2):
				for o in range(3):
					for r in range(500):
						min_cache[r1][r2][r3][o][r] = -1


def calcFreq():
	print("in calcFreq")
	valPA = stats['valAB'] + stats['valBB']
	valTOB = stats['valH'] + stats['valBB']
	val1B = stats['valH'] - stats['val2B'] - stats['val3B'] - stats['valHR']

	valTB = stats['valH'] + stats['val2B'] + 2*stats['val3B'] + 3*stats['valHR']
	valOUT = stats['valAB'] - stats['valH']

	# create frequencies per PA for all variables
	frq['freqOBP'] = valTOB / (valPA * 1.0)
	frq['freqBB'] = stats['valBB'] / (valPA * 1.0)
	frq['freq1B'] = val1B / (valPA * 1.0)
	frq['freq2B'] = stats['val2B'] / (valPA * 1.0)
	frq['freq3B'] = stats['val3B'] / (valPA * 1.0)
	frq['freqHR'] = stats['valHR'] / (valPA * 1.0)
	frq['freqSO'] = stats['valBB'] / (valPA * 1.0)
	frq['freqOUT'] = 1.0 - (frq['freqOBP'] * 1.0)

	frq['freqH'] = stats['valH'] / (valPA * 1.0)
	freqTB = frq['freq1B'] + (2*frq['freq2B']) + (3*frq['freq3B']) + (4*frq['freqHR'])

	# calculate number of PA per 27-out game
	frq['freqPA'] = frq['freqOBP']/(frq['freqOUT'] * 27.0) + 27.0

	# percentage of non K outs to all outs
	frq['rateNonK_OUT'] = 1 - frq['freqSO']/frq['freqOUT']

	# SLG, BA
	rateSLG = (frq['freq1B'] + (2*frq['freq2B']) + (3*frq['freq3B']) + (4*frq['freqHR'])) / (1 - frq['freqBB'])
	rateBA = (frq['freq1B'] + frq['freq2B'] + frq['freq3B'] + frq['freqHR']) / (1 - frq['freqBB'])


def reEngine():
	# chance of *not* scoring for each state
	# the variable name is of the form:
	# - state_bb_o_r, where
	# --- bb = base of the lead runner
	# --- o = number of outs
	# --- r = number of other runners on base
	print("in reEngine")

	state_3b_2_2 = frq['freqOUT']
	state_3b_2_1 = state_3b_2_2*frq['freqBB'] + frq['freqOUT']
	state_3b_2_0 = state_3b_2_1*frq['freqBB'] + frq['freqOUT']

	state_3b_1_2 = state_3b_2_2*frq['freqOUT']*(1-frq['rateNonK_OUT']*eventOUT_state3B_1)
	state_3b_1_1 = state_3b_1_2*frq['freqBB'] + state_3b_2_1*frq['freqOUT']*(1-frq['rateNonK_OUT']*eventOUT_state3B_1)
	state_3b_1_0 = state_3b_1_1*frq['freqBB'] + state_3b_2_0*frq['freqOUT']*(1-frq['rateNonK_OUT']*eventOUT_state3B_1)

	state_3b_0_2 = state_3b_1_2*frq['freqOUT']*(1-frq['rateNonK_OUT']*eventOUT_state3B_0)
	state_3b_0_1 = state_3b_0_2*frq['freqBB'] + state_3b_1_1*frq['freqOUT']*(1-frq['rateNonK_OUT']*eventOUT_state3B_0)
	state_3b_0_0 = state_3b_0_1*frq['freqBB'] + state_3b_1_0*frq['freqOUT']*(1-frq['rateNonK_OUT']*eventOUT_state3B_0)

	state_2b_2_1 = state_3b_2_2*(frq['freqBB']+frq['freq1B']*(1-event1B_state2B_2)) + frq['freqOUT']
	state_2b_2_0 = state_2b_2_1*frq['freqBB'] + state_3b_2_1*frq['freq1B']*(1-event1B_state2B_2) + frq['freqOUT']


	state_2b_1_1 = state_3b_1_2*(frq['freqBB']+frq['freq1B']*(1-event1B_state2B_1)) \
		+ state_3b_2_1*frq['freqOUT']*frq['rateNonK_OUT']*eventOUT_state2B_1 \
		+ state_2b_2_1*frq['freqOUT']*(1-frq['rateNonK_OUT']*eventOUT_state2B_1)

	state_2b_1_0 = state_2b_1_1*frq['freqBB'] \
		+ state_3b_1_1*frq['freq1B']*(1-event1B_state2B_1) \
		+ state_3b_2_0*frq['freqOUT']*frq['rateNonK_OUT']*eventOUT_state2B_1 \
		+ state_2b_2_0*frq['freqOUT']*(1-frq['rateNonK_OUT']*eventOUT_state2B_1)


	state_2b_0_1 = state_3b_0_2*(frq['freqBB']+frq['freq1B']*(1-event1B_state2B_0)) \
		+ state_3b_1_1*frq['freqOUT']*frq['rateNonK_OUT']*eventOUT_state2B_0 \
		+ state_2b_1_1*frq['freqOUT']*(1-frq['rateNonK_OUT']*eventOUT_state2B_0)

	state_2b_0_0 = state_2b_0_1*frq['freqBB'] \
		+ state_3b_0_1*frq['freq1B']*(1-event1B_state2B_0) \
		+ state_3b_1_0*frq['freqOUT']*frq['rateNonK_OUT']*eventOUT_state2B_0 \
		+ state_2b_1_0*frq['freqOUT']*(1-frq['rateNonK_OUT']*eventOUT_state2B_0)


	state_1b_2_0 = state_2b_2_1*(frq['freqBB']+frq['freq1B']*(1-event1B_state1B_2)) \
		+ state_3b_2_1*(frq['freq1B']*(event1B_state1B_2)+frq['freq2B']*(1-event2B_state1B_2)) \
		+ frq['freqOUT']

	state_1b_1_0 = state_2b_1_1*(frq['freqBB']+frq['freq1B']*(1-event1B_state1B_1)) \
		+ state_3b_1_1*(frq['freq1B']*(event1B_state1B_1)+frq['freq2B']*(1-event2B_state1B_1)) \
		+ state_2b_2_0*frq['freqOUT']*frq['rateNonK_OUT']*eventOUT_state1B_1 \
		+ state_1b_2_0*frq['freqOUT']*(1-frq['rateNonK_OUT']*eventOUT_state1B_1)

	state_1b_0_0 = state_2b_0_1*(frq['freqBB']+frq['freq1B']*(1-event1B_state1B_0)) \
		+ state_3b_0_1*(frq['freq1B']*(event1B_state1B_0)+frq['freq2B']*(1-event2B_state1B_0)) \
		+ state_2b_1_0*frq['freqOUT']*frq['rateNonK_OUT']*eventOUT_state1B_0 \
		+ state_1b_1_0*frq['freqOUT']*(1-frq['rateNonK_OUT']*eventOUT_state1B_0)

	# chance of scoring from a triple, single, double
	#   The "_2" and "_1" extensions to each variable is required for the RE calculations
	#   and is too long to myEXPlain here.  In short, its the number of outs in an inning
	chance3B_3 = 1 - (state_3b_2_0 + state_3b_1_0 + state_3b_0_0) / 3.0
	chance2B_3 = 1 - (state_2b_2_0 + state_2b_1_0 + state_2b_0_0) / 3.0
	chance1B_3 = 1 - (state_1b_2_0 + state_1b_1_0 + state_1b_0_0) / 3.0

	chance3B_2 = 1 - (state_3b_2_0 + state_3b_1_0) / 2.0
	chance2B_2 = 1 - (state_2b_2_0 + state_2b_1_0) / 2.0
	chance1B_2 = 1 - (state_1b_2_0 + state_1b_1_0) / 2.0

	chance3B_1 = 1 - (state_3b_2_0) / 1.0
	chance2B_1 = 1 - (state_2b_2_0) / 1.0
	chance1B_1 = 1 - (state_1b_2_0) / 1.0

	# number of times a runner scores after getting on base from a HR, 3B, 2B, 1B, BB
	runsHR = frq['freqHR']
	runs3B_3 = chance3B_3 * frq['freq3B']
	runs2B_3 = chance2B_3 * frq['freq2B']
	runs1B_3 = chance1B_3 * (frq['freq1B'] + frq['freqBB'])

	runs3B_2 = chance3B_2 * frq['freq3B']
	runs2B_2 = chance2B_2 * frq['freq2B']
	runs1B_2 = chance1B_2 * (frq['freq1B'] + frq['freqBB'])

	runs3B_1 = chance3B_1 * frq['freq3B']
	runs2B_1 = chance2B_1 * frq['freq2B']
	runs1B_1 = chance1B_1 * (frq['freq1B'] + frq['freqBB'])

	# total number of runs scored in a game
	runsALL = (runsHR + runs3B_3 + runs2B_3 + runs1B_3) * frq['freqPA']

	# the "bases empty" line for the Run Expectancy matrix, for 0, 1, 2 outs
	rpi_3 = (runsHR + runs3B_3 + runs2B_3 + runs1B_3) * frq['freqPA'] / 9.0
	rpi_2 = (runsHR + runs3B_2 + runs2B_2 + runs1B_2) * frq['freqPA'] * (2.0/3.0) / 9.0
	rpi_1 = (runsHR + runs3B_1 + runs2B_1 + runs1B_1) * frq['freqPA'] * (1.0/3.0) / 9.0

	# the rest of the run expectancy matrix
	RE_1xx_0 = (1 - state_1b_0_0) + rpi_3
	RE_1xx_1 = (1 - state_1b_1_0) + rpi_2
	RE_1xx_2 = (1 - state_1b_2_0) + rpi_1

	RE_x2x_0 = (1 - state_2b_0_0) + rpi_3
	RE_x2x_1 = (1 - state_2b_1_0) + rpi_2
	RE_x2x_2 = (1 - state_2b_2_0) + rpi_1

	RE_xx3_0 = (1 - state_3b_0_0) + rpi_3
	RE_xx3_1 = (1 - state_3b_1_0) + rpi_2
	RE_xx3_2 = (1 - state_3b_2_0) + rpi_1

	RE_12x_0 = (1 - state_1b_0_0) + (1 - state_2b_0_1) + rpi_3
	RE_12x_1 = (1 - state_1b_1_0) + (1 - state_2b_1_1) + rpi_2
	RE_12x_2 = (1 - state_1b_2_0) + (1 - state_2b_2_1) + rpi_1

	RE_1x3_0 = (1 - state_1b_0_0) + (1 - state_3b_0_1) + rpi_3
	RE_1x3_1 = (1 - state_1b_1_0) + (1 - state_3b_1_1) + rpi_2
	RE_1x3_2 = (1 - state_1b_2_0) + (1 - state_3b_2_1) + rpi_1

	RE_x23_0 = (1 - state_2b_0_0) + (1 - state_3b_0_1) + rpi_3
	RE_x23_1 = (1 - state_2b_1_0) + (1 - state_3b_1_1) + rpi_2
	RE_x23_2 = (1 - state_2b_2_0) + (1 - state_3b_2_1) + rpi_1

	RE_123_0 = (1 - state_1b_0_0) + (1 - state_2b_0_1) + (1 - state_3b_0_2) + rpi_3
	RE_123_1 = (1 - state_1b_1_0) + (1 - state_2b_1_1) + (1 - state_3b_1_2) + rpi_2
	RE_123_2 = (1 - state_1b_2_0) + (1 - state_2b_2_1) + (1 - state_3b_2_2) + rpi_1

	# the "bases empty" line for the Run Frequency matrix, for 0, 1, 2 outs
	RF_xxx_2 = (frq['freqHR'] + frq['freq3B']*(1-state_3b_2_0) + frq['freq2B']*(1-state_2b_2_0) + (frq['freq1B']+frq['freqBB'])*(1-state_1b_2_0))
	RF_xxx_1 = (frq['freqHR'] + frq['freq3B']*(1-state_3b_1_0) + frq['freq2B']*(1-state_2b_1_0) + (frq['freq1B']+frq['freqBB'])*(1-state_1b_1_0)) + frq['freqOUT']*RF_xxx_2
	RF_xxx_0 = (frq['freqHR'] + frq['freq3B']*(1-state_3b_0_0) + frq['freq2B']*(1-state_2b_0_0) + (frq['freq1B']+frq['freqBB'])*(1-state_1b_0_0)) + frq['freqOUT']*RF_xxx_1

	# the rest of the run frequency matrix
	RF_1xx_0 = 1 - state_1b_0_0
	RF_1xx_1 = 1 - state_1b_1_0
	RF_1xx_2 = 1 - state_1b_2_0

	RF_x2x_0 = 1 - state_2b_0_0
	RF_x2x_1 = 1 - state_2b_1_0
	RF_x2x_2 = 1 - state_2b_2_0

	RF_xx3_0 = 1 - state_3b_0_0
	RF_xx3_1 = 1 - state_3b_1_0
	RF_xx3_2 = 1 - state_3b_2_0

	RF_12x_0 = 1 - state_2b_0_1
	RF_12x_1 = 1 - state_2b_1_1
	RF_12x_2 = 1 - state_2b_2_1

	RF_1x3_0 = 1 - state_3b_0_1
	RF_1x3_1 = 1 - state_3b_1_1
	RF_1x3_2 = 1 - state_3b_2_1

	RF_x23_0 = 1 - state_3b_0_1
	RF_x23_1 = 1 - state_3b_1_1
	RF_x23_2 = 1 - state_3b_2_1

	RF_123_0 = 1 - state_3b_0_2
	RF_123_1 = 1 - state_3b_1_2
	RF_123_2 = 1 - state_3b_2_2

	# wes - expanded run frequency matrix
	# rfs[b1][b2][b3][out] is frequency of scoring (at least 1 run) from a base out state
	#  through the end of the inning
	# similar to the RF_BBB_O variables above

	rfs[0][0][0][0] = (frq['freqHR'] + frq['freq3B']*(1-state_3b_0_0) + frq['freq2B']*(1-state_2b_0_0) + (frq['freq1B']+frq['freqBB'])*(1-state_1b_0_0)) + frq['freqOUT']*RF_xxx_1
	rfs[0][0][0][1] = (frq['freqHR'] + frq['freq3B']*(1-state_3b_1_0) + frq['freq2B']*(1-state_2b_1_0) + (frq['freq1B']+frq['freqBB'])*(1-state_1b_1_0)) + frq['freqOUT']*RF_xxx_2
	rfs[0][0][0][2] = (frq['freqHR'] + frq['freq3B']*(1-state_3b_2_0) + frq['freq2B']*(1-state_2b_2_0) + (frq['freq1B']+frq['freqBB'])*(1-state_1b_2_0))

	rfs[1][0][0][0] = (1 - state_1b_0_0)
	rfs[1][0][0][1] = (1 - state_1b_1_0)
	rfs[1][0][0][2] = (1 - state_1b_2_0)
	rfs[0][1][0][0] = (1 - state_2b_0_0)
	rfs[0][1][0][1] = (1 - state_2b_1_0)
	rfs[0][1][0][2] = (1 - state_2b_2_0)
	rfs[0][0][1][0] = (1 - state_3b_0_0)
	rfs[0][0][1][1] = (1 - state_3b_1_0)
	rfs[0][0][1][2] = (1 - state_3b_2_0)
	rfs[1][1][0][0] = (1 - state_2b_0_1)
	rfs[1][1][0][1] = (1 - state_2b_1_1)
	rfs[1][1][0][2] = (1 - state_2b_2_1)
	rfs[1][0][1][0] = (1 - state_3b_0_1)
	rfs[1][0][1][1] = (1 - state_3b_1_1)
	rfs[1][0][1][2] = (1 - state_3b_2_1)
	rfs[0][1][1][0] = (1 - state_3b_0_1)
	rfs[0][1][1][1] = (1 - state_3b_1_1)
	rfs[0][1][1][2] = (1 - state_3b_2_1)
	rfs[1][1][1][0] = (1 - state_3b_0_2)
	rfs[1][1][1][1] = (1 - state_3b_1_2)
	rfs[1][1][1][2] = (1 - state_3b_2_2)
	
	return runsALL

# function - rf_min
# calculate the chance of scoring at least N runs from a given base/out state
# through the remainder of the inning
def rf_min(b1,b2,b3,out,runs):
	print("in rf_min")
	if min_cache[b1][b2][b3][out][runs] >= 0:
		min_use_count += 1
		return min_cache[b1][b2][b3][out][runs]

	# array to represent the baserunners
	# b[1] is the location of the lead runner, b[2] is location of a second runner, etc.

	b = [0]*4

	if runs == 1:
		alertString = "runs = 1  and br:"+b1+b2+b3+" and outs = "+out+" returning rfs["+b1+","+b2+","+b3+","+out+"] = "+rfs[b1][b2][b3][out]
		print(alertString)
		min_return = rfs[b1][b2][b3][out]

	if runs == 0:
		alertString = "runs = 0; returning 1"
		print(alertString)
		min_return = 1

	# runs > 1
	# print("runs > 1");
	br = b1+b2+b3

	if b3 == 1:
		b[1] = 3
	if b2 == 1:
		if b[1] > 0:
			b[2] = 2
		else:
			b[1] = 2

	if b1 == 1:
		if b[2] > 0:
			b[3] = 1
		else:
			if (b[1] > 0):
				b[2] = 1
			else:
				b[1] = 1

	if br >= runs:
		#  need to score the runner representing the final of the desired runs
		#  e.g.  if looking to score 2 -> b[2], to score 3 -> b[3]
		if runs == 3:
			# chance of scoring from first (third runner)
			alertString = "(runs =  "+runs+" and br:"+b1+b2+b3+" and out = "+out+" returning rfs[1,0,0,out] = "+rfs[1][0][0][out]
			print(alertString)
			min_return = rfs[1][0][0][out]
		elif runs == 2:
			if b[2] == 2:
				if b[3] > 1:
					alertString = "(runs =  "+runs+" and br:"+b1+b2+b3+" and out = "+out+" returning rfs[1,1,0,out] = "+rfs[1][1][0][out]
					print(alertString)
					min_return = rfs[1][1][0][out]
				else:
					alertString = "(runs =  "+runs+" and br:"+b1+b2+b3+" and out = "+out+" returning rfs[0,1,0,out] = "+rfs[0][1][0][out]
					print(alertString)
					min_return = rfs[0][1][0][out]
			else:
				# second runner is on first
				alertString = "(runs =  "+runs+" and br:"+b1+b2+b3+" and out = "+out+" returning rfs[1,0,0,out] = "+rfs[1][0][0][out]
				print(alertString)
				min_return = rfs[1][0][0][out]
	else: # br < runs
		if (runs - br) == 1:
			min_return = rfs[0][0][0][out]
		else: # run - br > 1
			chance = 0

			for o in range(out, 3):
				chance = chance + myEXP(frq['freqOBP'], runs-br-1) * myEXP(frq['freqOUT'], o - out) * ob_permutations(o-out, runs-br-2, 0) * rfs[0][0][0][o]

			alertString = "(runs =  "+runs+" and br:"+b1+b2+b3+" and out = "+out+" returning chance = "+chance
			print(alertString)
			min_return = chance

	# need to populate cache here
	min_cache[b1][b2][b3][out][runs] = min_return
	min_add_count += 1
	return min_return

#
#  function - rf_exact
#  calculate the chance of scoring exactly N runs from a given base/out state
#  example -  	chance of scoring exactly 3 runs from a runner on third, 2 out state
#  			rf_exact(0,0,1,2,3) = (chance of scoring at least 3) - (chance of scoring at least 4)
def rf_exact(b1, b2, b3, out, runs):
	if exact_cache[b1][b2][b3][out][runs] >= 0:
		exact_use_count += 1
		return exact_cache[b1][b2][b3][out][runs]

	r_value = rf_min(b1,b2,b3,out,runs)
	r1_value = rf_min(b1,b2,b3,out,runs + 1)

	ret_value = r_value - r1_value

	if (r_value < r1_value):
		alertString = "rf_min("+b1+","+b2+","+b3+","+out+","+runs+") = "+r_value
		alertString = alertString + "rf_min("+b1+","+b2+","+b3+","+out+","+(runs+1)+") = "+r1_value
		print(alertString)

	#  need to populate cache here
	exact_cache[b1][b2][b3][out][runs] = ret_value
	exact_add_count += 1

	return ret_value

def calcEstimators():
	print("in calcEstimators")
	# this is for fun.  I calculate BaseRuns and basic Runs Created
	valA = frq['freqBB'] + frq['freq1B'] + frq['freq2B'] + frq['freq3B']
	valB = .8*frq['freq1B'] + 2.0*frq['freq2B'] + 3.2*frq['freq3B'] + 1.8*frq['freqHR'] + .1*frq['freqBB']
	scoreRate = valB / (valB + frq['freqOUT'])
	BSR = (valA * scoreRate + frq['freqHR']) * frq['freqPA']
	BJRC = frq['freqOBP'] * (frq['freq1B'] + 2*frq['freq2B'] + 3*frq['freq3B'] + 4*frq['freqHR']) * frq['freqPA']
	return (BSR,BJRC)


#
# function - ob_permutations
# calculate the number of combinations to get a specified number of baserunners and outs
# example 1 baserunner reaching in 2 outs
# 100, 010, 001 -->  3 combinations

def ob_permutations(outs, base_runners):
	print("in ob_permutations")
	# check the cache to see if weve calculated this value already
	# if so, return the cached value
	if ob_perm_cache[outs][base_runners] >= 0:
		ob_use_count = ob_use_count +1
		return ob_perm_cache[outs][base_runners]

	perms = 0

	pa = base_runners + outs

	if base_runners == 0:
		perms = 1

	if base_runners == 1:
		perms = base_runners + outs

	if base_runners > 1:
		if (outs == 0):
			perms = 1
		else:  # outs > 0 and base_runners > 1
			recOuts.push(outs)
			recBR.push(base_runners)
			recPerms.push(perms)

			permResult = ob_permutations(outs , base_runners -1)

			perms = permResult + recPerms.pop()

			recPerms.push(perms)

			outs = recOuts.pop()
			base_runners = recBR.pop()

			recOuts.push(outs)
			recBR.push(base_runners)

			permResult = ob_permutations(outs - 1, base_runners )

			perms = permResult + recPerms.pop()

			outs = recOuts.pop()
			base_runners = recBR.pop()

	# cache the calculated value
	ob_perm_cache[outs][base_runners] = perms
	ob_add_count = ob_add_count +1
	return perms


#
#  function pWoolnerStack
#
#  calculate the chance of scoring N runs over a specified number of innings
#  this is implemented following a formula presented
#  by Keith Woolner in the Baseball Prospectus 2005 ed.
#  "An Analytical Framework for Win Expectancy" p. 524
#  note : the stack is used to control variables during recursion

def pWoolnerStack(runs, innings):
	print("in pWoolnerStack")
	# check the cache to see if weve calculated this value already
	# if so, return the cached value
	if woolner_cache[innings][runs] >= 0:
		return woolner_cache[innings][runs]

	if innings == 0:
		print("innings == 0")
		if runs == 0:
			retVal = 1
		else:
			retVal = 0
	else:
		print("innings != 0")

		retVal = 0

		iter = 0
		while iter <= runs:
			alertString = "about to push onto stack runs = "+runs+" innings = "+innings+" iter = "+iter+" retVal = "+retVal
			# print(alertString);

			recIter.push(iter)
			recRetVal.push(retVal)
			recRuns.push(runs)
			recInnings.push(innings)

			recResult = pWoolnerStack(runs - iter, innings - 1)

			iter = recIter.pop()
			retVal = recRetVal.pop() + rf_exact(0,0,0,0,iter) * recResult
			runs = recRuns.pop()
			innings = recInnings.pop()

			iter = iter + 1

		print("were past the while loop")

	alertString = "pWoolnerStack("+runs+","+innings+") = "+retVal
	print(alertString)

	# cache the calculated value
	woolner_cache[innings][runs] = retVal
	return retVal


def calcRuns():
	# processing data to determine
	# - runs scored per game
	# - run Expectancy matrix

	calcFreq()
	runsALL = reEngine()
	(BSR,BJRC) = calcEstimators()

	prepopulate_caches()

	# calculate LWTS
	baselineR = runsALL
	baselinePA = frq['freqPA']
	baselineBSR = BSR
	baselineBJRC = BJRC
	pebble = frq['freqPA'] / 100.0
	print(pebble)

	stats['valBB'] = stats['valBB'] + pebble
	calcFreq()
	runsALL =reEngine()
	(BSR,BJRC) = calcEstimators()
	lwtsBB = ((runsALL - baselineR) / (frq['freqPA'] - baselinePA) )
	bsrBB = ((BSR - baselineBSR) / (frq['freqPA'] - baselinePA) )
	bjrcBB = ((BJRC - baselineBJRC) / (frq['freqPA'] - baselinePA) )
	stats['valBB'] = stats['valBB'] - pebble

	stats['valAB'] = stats['valAB'] + pebble
	stats['valH'] = stats['valH'] + pebble
	calcFreq()
	runsALL = reEngine()
	(BSR,BJRC) = calcEstimators()
	lwts1B = ((runsALL - baselineR) / (frq['freqPA'] - baselinePA) )
	bjrc1B = ((BJRC - baselineBJRC) / (frq['freqPA'] - baselinePA) )
	bsr1B = ((BSR - baselineBSR) / (frq['freqPA'] - baselinePA) )

	stats['val2B'] = stats['val2B'] + pebble
	calcFreq()
	runsALL = reEngine()
	(BSR,BJRC) = calcEstimators()
	lwts2B = ((runsALL - baselineR) / (frq['freqPA'] - baselinePA) )
	bsr2B = ((BSR - baselineBSR) / (frq['freqPA'] - baselinePA) )
	bjrc2B = ((BJRC - baselineBJRC) / (frq['freqPA'] - baselinePA) )
	stats['val2B'] = stats['val2B'] - pebble

	stats['val3B'] = stats['val3B'] + pebble
	calcFreq()
	runsALL = reEngine()
	(BSR,BJRC) = calcEstimators()
	lwts3B = ((runsALL - baselineR) / (frq['freqPA'] - baselinePA) )
	bsr3B = ((BSR - baselineBSR) / (frq['freqPA'] - baselinePA) )
	bjrc3B = ((BJRC - baselineBJRC) / (frq['freqPA'] - baselinePA) )
	stats['val3B'] = stats['val3B'] - pebble

	stats['valHR'] = stats['valHR'] + pebble
	calcFreq()
	runsALL = reEngine()
	(BSR,BJRC) = calcEstimators()
	lwtsHR = ((runsALL - baselineR) / (frq['freqPA'] - baselinePA) )
	bsrHR = ((BSR - baselineBSR) / (frq['freqPA'] - baselinePA) )
	bjrcHR = ((BJRC - baselineBJRC) / (frq['freqPA'] - baselinePA) )
	stats['valHR'] = stats['valHR'] - pebble
	stats['valH'] = stats['valH'] - pebble
	stats['valAB'] = stats['valAB'] - pebble

	stats['valBB'] = stats['valBB'] + pebble
	calcFreq()
	runsALL = reEngine()
	(BSR,BJRC) = calcEstimators()
	lwtsSO = (runsALL - baselineR) / pebble
	stats['valBB'] = stats['valBB'] - pebble

	lwtsOUT = -1*(frq['freqBB']*lwtsBB \
			   + frq['freq1B']*lwts1B \
			   + frq['freq2B']*lwts2B \
			   + frq['freq3B']*lwts3B \
			   + frq['freqHR']*lwtsHR \
			   + frq['freqSO']*lwtsSO) / frq['freqOUT']

	rcOUT = lwtsOUT + runsALL/27

calcRuns()
