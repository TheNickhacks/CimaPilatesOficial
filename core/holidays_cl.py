import json
from datetime import date, timedelta
from functools import lru_cache
from urllib.request import urlopen


def _easter_sunday(year):
	a = year % 19
	b = year // 100
	c = year % 100
	d = b // 4
	e = b % 4
	f = (b + 8) // 25
	g = (b - f + 1) // 3
	h = (19 * a + b - d - g + 15) % 30
	i = c // 4
	k = c % 4
	l = (32 + 2 * e + 2 * i - h - k) % 7
	m = (a + 11 * h + 22 * l) // 451
	month = (h + l - 7 * m + 114) // 31
	day = ((h + l - 7 * m + 114) % 31) + 1
	return date(year, month, day)


def _fallback_holidays(year):
	holidays = {}
	def add(d, name):
		holidays[d] = name

	add(date(year, 1, 1), "Año Nuevo")
	add(date(year, 5, 1), "Día del Trabajador")
	add(date(year, 5, 21), "Glorias Navales")
	add(date(year, 6, 29), "San Pedro y San Pablo")
	add(date(year, 7, 16), "Virgen del Carmen")
	add(date(year, 8, 15), "Asunción de la Virgen")
	add(date(year, 9, 18), "Independencia Nacional")
	add(date(year, 9, 19), "Glorias del Ejército")
	add(date(year, 10, 12), "Encuentro de Dos Mundos")
	add(date(year, 10, 31), "Día de las Iglesias Evangélicas y Protestantes")
	add(date(year, 11, 1), "Día de Todos los Santos")
	add(date(year, 12, 8), "Inmaculada Concepción")
	add(date(year, 12, 25), "Navidad")

	easter = _easter_sunday(year)
	add(easter - timedelta(days=2), "Viernes Santo")
	add(easter - timedelta(days=1), "Sábado Santo")
	return holidays


@lru_cache(maxsize=16)
def get_holidays(year):
	try:
		with urlopen(f"https://date.nager.at/api/v3/PublicHolidays/{year}/CL", timeout=2) as response:
			data = json.loads(response.read().decode("utf-8"))
		holidays = {}
		for item in data:
			try:
				iso_date = item.get("date")
				y, m, d = (int(part) for part in iso_date.split("-"))
				holidays[date(y, m, d)] = item.get("localName") or item.get("name") or "Feriado"
			except Exception:
				continue
		if holidays:
			return holidays
	except Exception:
		pass
	return _fallback_holidays(year)


def get_holiday_name(target_date):
	return get_holidays(target_date.year).get(target_date)


def is_holiday(target_date):
	return get_holiday_name(target_date) is not None

