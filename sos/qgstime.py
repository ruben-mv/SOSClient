# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QgsTime... classes
                             -------------------
        begin                : 2014-11-26
        copyright            : (C) 2014 by Rubén Mosquera Varela
        email                : ruben.mosquera.varela@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import abc
from dateutil import parser as DateTimeParser
from datetime import datetime
#import pytz

class QgsTime (object):
    __metadata__ = abc.ABCMeta

    TimeInstant = 1
    TimePeriod = 2
    
    @abc.abstractmethod
    def __init__(self, timePrimitive=0):
        self._timePrimitive = timePrimitive
        self._values = ["latest" for _ in range(timePrimitive)]
        
    def _parse (self, dt):
        '''
        
        :param dt:
        '''
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
    def __init__(self, time=""):
        super(QgsTimeInstant, self).__init__(QgsTime.TimeInstant)
        self._values[0] = self._parse(time)
    
    @property
    def date (self):
        return self._getDate(0)
    
    @property
    def time (self):
        return self._getTime(0)