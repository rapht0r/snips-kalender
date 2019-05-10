from hermes_python.ontology.dialogue import InstantTimeValue
from datetime import date, datetime, timedelta, timezone
import caldav
from caldav.elements import dav, cdav
from dateutil.rrule import *
from pytz import timezone
import collections

import requests
import urllib.request
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import icalendar

class Calendar:
  def __init__(self, config):
    try:
        self.url = config['secret']['caldav_url']
        self.user = config['secret']['user']
        self.password = config['secret']['password']
        self.verify = config['secret']['ssl_verify'] in ['True', 'true']
    except KeyError:
        print("Fehler in der Konfigurationsdatei")

  def checkDateTime(self, item):
   return item if isinstance(item, datetime) else datetime(item.year, item.month, item.day).replace(tzinfo=timezone('Europe/Amsterdam')) 

  def getAppointment(self, intentMessage):
    when = datetime.today()
    if not intentMessage.slots or not intentMessage.slots.items():
      return "Ich habe das Datum leider nicht verstanden"

    for (slot_name, slot) in intentMessage.slots.items():
      if slot_name not in ['date']:
        return "Unbekannter Slotname " + slot_name
      if not isinstance(slot[0].slot_value.value, InstantTimeValue):
        return "Die Slotart wird nicht unterstützt"
      else:
        when = datetime.strptime(slot[0].slot_value.value.value[:-7], '%Y-%m-%d %H:%M:%S')
    when = when.replace(tzinfo=timezone('Europe/Amsterdam'))
    until = when + timedelta(hours=23, minutes=59)

    try:
      client = caldav.DAVClient(self.url, None, self.user, self.password, None, self.verify)
      calendars = client.principal().calendars()
    except caldav.lib.error.AuthorizationError:
      return "Die konfigurierten Anmeldedaten sind ungültig."
    except requests.exceptions.ConnectionError:
      return "Die Verbindung zum Server konnte nicht hergestellt werden."
 
    if len(calendars) > 0:
      response = ""
      calendar = calendars[0]
      print("Using calendar ", calendar, " looking for events in range " + when.strftime("%m/%d/%Y, %H:%M:%S") + " and " + until.strftime("%m/%d/%Y, %H:%M:%S"))
      try: 
        events = calendar.date_search(when, until)
        result = {}
        resultNoTime = {}
        for event in events:
          event.load()
          print ("Found ", str(event))
          gcal = icalendar.Calendar.from_ical(event._get_data())
          for component in gcal.walk():
            if component.name == "VEVENT":
              summary = component.get('summary')
              startdt = component.get('dtstart').dt
              if component.get('dtend') is not None:
                enddt = component.get('dtend').dt
              else:
                enddt = until 
              exdate = component.get('exdate')
              if component.get('rrule'):
                reoccur = component.get('rrule').to_ical().decode('utf-8')
                for item in self.parse_recurrences(reoccur, startdt, when, until, exdate):
                  print("{0}: {1} ".format(item.strftime("%H:%M Uhr"), summary))
                  self.storeItem(result, resultNoTime, item, enddt, summary, when)
              else:
                print("{0}: {1}".format(startdt.strftime("%H:%M Uhr"), summary))
                self.storeItem(result, resultNoTime, startdt, enddt, summary, when)
        print(resultNoTime)
        print(result)
        for key, value in resultNoTime.items():
          response += "{0} ".format(value)
        for key, value in collections.OrderedDict(sorted(result.items())).items():
          response += "{0}: {1} ".format(key.strftime("%H:%M Uhr"), value)
        print(response)
        return response
      except caldav.lib.error.NotFoundError:
        return "Keine Termine im Kalender gefunden"
    else:
      return "Ich habe keinen Kalender gefunden." 

  def storeItem(self, result, resultNoTime, startdt, enddt, summary, when):
    if type(startdt) is date:
      if enddt > when.date():
        resultNoTime[startdt] = summary
    else:
      result[startdt] = summary

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
    return rules.between(start - timedelta(minutes=1), end)
