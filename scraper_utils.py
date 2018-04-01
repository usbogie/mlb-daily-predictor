from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, date
import urllib.request as request
import urllib.error as error

team_codes = {
	"Arizona Diamondbacks": "ari",
	"Atlanta Braves": "atl",
	"Baltimore Orioles": "bal",
	"Boston Red Sox": "bos",
	"Chicago Cubs": "chn",
	"Chicago White Sox": "cha",
	"Cincinnati Reds": "cin",
	"Cleveland Indians": "cle",
	"Colorado Rockies": "col",
	"Detroit Tigers": "det",
	"Houston Astros": "hou",
	"Kansas City Royals": "kca",
	"Los Angeles Angels": "ana",
	"Los Angeles Dodgers": "lan",
	"Miami Marlins": "mia",
	"Milwaukee Brewers": "mil",
	"Minnesota Twins": "min",
	"New York Mets": "nyn",
	"New York Yankees": "nya",
	"Oakland Athletics": "oak",
	"Philadelphia Phillies": "phi",
	"Pittsburgh Pirates": "pit",
	"San Diego Padres": "sdn",
	"San Francisco Giants": "sfn",
	"Seattle Mariners": "sea",
	"St. Louis Cardinals": "sln",
	"Tampa Bay Rays": "tba",
	"Texas Rangers": "tex",
	"Toronto Blue Jays": "tor",
	"Washington Nationals": "was",
}

def get_soup(url):
	ua = UserAgent()
	try:
		page = request.urlopen(request.Request(url, headers = { 'User-Agent' : ua.random }))
	except (ConnectionResetError, error.URLError, error.HTTPError) as e:
		try:
			wait_time = round(max(10, 12 + random.gauss(0,1)), 2)
			time.sleep(wait_time)
			print("First attempt for %s failed. Trying again." % (url))
			page = request.urlopen(request.Request(url, headers = { 'User-Agent' : ua.random }))
		except:
			print(e)
			sys.exit()
	content = page.read()
	return BeautifulSoup(content, "html5lib")

def get_days_in_season(year):
	opening_days = {2017:'2017-04-02'}
	closing_days = {2017:'2017-10-01'}
	months = ['04', '05', '06', '07', '08', '09', '10']
	dates = {'04': list(range(31)[1:]), '05': list(range(32)[1:]), '06': list(range(31)[1:]),
			 '07': list(range(32)[1:]), '08': list(range(32)[1:]), '09': list(range(31)[1:]),
			 '10': list(range(32)[1:])}

	all_season = []
	for month in months:
		for d in dates[month]:
			day = str(d)
			if len(day) == 1:
				day = '0'+day
			date = "{}-{}-{}".format(year,month,day)
			if date < opening_days[year] or date > closing_days[year]:
				continue
			all_season.append(date)

	return all_season
