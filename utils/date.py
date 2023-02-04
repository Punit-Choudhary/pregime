from datetime import datetime, date, timedelta


def get_yday():
  return datetime.today().strftime('%j')


def get_date(yday):
  yday.rjust(3 + len(yday), '0')
  year = datetime.today().strftime("%Y")

  start_date = date(int(year), 1, 1)
  res_date = start_date + timedelta(days=int(yday) - 1)
  res_date = res_date.strftime("%d-%m-%Y")

  return res_date
