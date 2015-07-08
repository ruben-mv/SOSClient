# -*- coding: utf-8 -*-
"""
 QgsTime... classes
"""

import abc
from dateutil import parser as DateTimeParser
from datetime import datetime
#import pytz

class QgsTime (object):
    """
    Abstract base class for QgsTime types
    """
    __metadata__ = abc.ABCMeta

    TimeInstant = 1
    TimePeriod = 2
    
    @abc.abstractmethod
    def __init__(self, timePrimitive=0):
        self._timePrimitive = timePrimitive
        self._values = ["latest" for _ in range(timePrimitive)]
        
    def _parse (self, dt):
        """
        :param dt: datetime, latest or first
        """
        if dt in ["latest", "first"]:
            return dt
        
        try:
            dt = DateTimeParser.parse(dt)
        except Exception:
            dt = datetime.today().date()
            #.utcnow()
            #dt.replace(tzinfo=pytz.utc)
        finally:
            return dt

    @property
    def primitive (self):
        return self._timePrimitive
    
    def _getDate (self, i):
        try:
            return self._values[i].date()
        except AttributeError:
            return self._values[i]
        except:
            return
        
    def _getTime (self, i):
        try:
            return self._values[i].time()
        except:
            return

    def __str__(self):
        toStr = lambda dt : dt if isinstance (dt, str) else str(dt).replace(" ", "T")
        return " ".join([toStr(dt) for dt in self._values])

class QgsTimePeriod (QgsTime):
    """
    Represents a time period with begin date and time and end date and time
    """
    def __init__(self, begin="", end=""):
        super(QgsTimePeriod, self).__init__(QgsTime.TimePeriod)
        self._values[0] = self._parse(begin)
        self._values[1] = self._parse(end)
    
    @property
    def beginDate (self):
        return self._getDate(0)
    
    @property
    def beginTime (self):
        return self._getTime(0)
    
    @property
    def endDate (self):
        return self._getDate(1)
    
    @property
    def endTime (self):
        return self._getTime(1)
    
class QgsTimeInstant (QgsTime):
    """
    Represents a time instant
    """
    def __init__(self, time=""):
        super(QgsTimeInstant, self).__init__(QgsTime.TimeInstant)
        self._values[0] = self._parse(time)
    
    @property
    def date (self):
        return self._getDate(0)
    
    @property
    def time (self):
        return self._getTime(0)