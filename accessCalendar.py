from datetime import datetime, timedelta, timezone
import caldav
from caldav.elements import dav, cdav
from dateutil.rrule import *
from pytz import timezone
import collections

import urllib.request
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import icalendar

class Calendar:
  def parse_recurrences(recur_rule, start, exclusions):
    """ Find all reoccuring events """
    rules = rruleset()
    first_rule = rrulestr(recur_rule, dtstart=start)
    rules.rrule(first_rule)
    if not isinstance(exclusions, list):
        exclusions = [exclusions]
        for xdate in exclusions:
            try:
                rules.exdate(xdate.dts[0].dt)
            except AttributeError:
                pass
    now = datetime.now(timezone.utc)
    this_year = now + timedelta(days=60)
    dates = []
    for rule in rules.between(now, this_year):
        dates.append(rule.strftime("%D %H:%M UTC "))
    return dates


  def __init__(self):
    # Caldav url
    self.url = "https://user:password@host:5006/share/Kalender"


  def getAppointment(self, intentMessage):
    when = datetime.today()
    if not intentMessage.slots.items():
      return "Ich habe das Datum leider nicht verstanden"

    for (slot_name, slot) in intentMessage.slots.items():
      if slot_name not in ['date']:
        return "Unbekannter Slotname " + slot_name
      else:
        when = datetime.strptime(slot[0].slot_value.value.value[:-7], '%Y-%m-%d %H:%M:%S')
    when = when.replace(tzinfo=timezone('Europe/Amsterdam'))
    until = when + timedelta(hours=23, minutes=59)

    self.client = caldav.DAVClient(self.url, None, None, None, None, False)
    self.calendars = self.client.principal().calendars()
    if len(self.calendars) > 0:
      response = ""
      self.calendar = self.calendars[0]
      print("Using calendar ", self.calendar, " looking for events in range " + when.strftime("%m/%d/%Y, %H:%M:%S") + " and " + until.strftime("%m/%d/%Y, %H:%M:%S"))
      try: 
        events = self.calendar.date_search(when, until)
        result = {}
        for event in events:
          event.load()
          print ("Found ", str(event))
          gcal = icalendar.Calendar.from_ical(event._get_data())
          for component in gcal.walk():
            if component.name == "VEVENT":
              summary = component.get('summary')
              startdt = component.get('dtstart').dt
              exdate = component.get('exdate')
              if component.get('rrule'):
                reoccur = component.get('rrule').to_ical().decode('utf-8')
                for item in self.parse_recurrences(reoccur, startdt, when, until, exdate):
                  result[item] = summary
              else:
#                result[datetime.combine(startdt, datetime.min.time())] = summary
                result[startdt] = summary
        print(result)
        result_sorted = collections.OrderedDict(sorted(result.items()))
        for key, value in result_sorted.items():
            response += "{0}: {1} ".format(key.strftime("%H:%M Uhr"), value)
        return response
      except caldav.lib.error.NotFoundError:
        return "Keine Termine im Kalender gefunden"

  def parse_recurrences(self, recur_rule, startdt, start, end, exclusions):
    """ Find all reoccuring events """
    rules = rruleset()
    first_rule = rrulestr(recur_rule, dtstart=startdt)
    rules.rrule(first_rule)
    if not isinstance(exclusions, list):
        exclusions = [exclusions]
        for xdate in exclusions:
            try:
                rules.exdate(xdate.dts[0].dt)
            except AttributeError:
                pass
    dates = []
#    for rule in rules.between(start.replace(tzinfo=timezone('Europe/Amsterdam')), end.replace(tzinfo=timezone('Europe/Amsterdam'))):
    for rule in rules.between(start - timedelta(minutes=1), end):
        dates.append(rule)
    return dates
