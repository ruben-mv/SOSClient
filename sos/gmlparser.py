# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GML...Parser classes
                             -------------------
        begin                : 2014-11-26
        copyright            : (C) 2014 by Rubén Mosquera Varela
        email                : ruben.mosquera.varela@gmail.com
 ***************************************************************************/
@author: Rubén Mosquera Varela
@contact: ruben.mosquera.varela@gmail.com
@copyright:
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free SoftwGMLTimeParser()are Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from xmlparser import XMLParser
import qgstime

class GMLTimeInstantParser (XMLParser):
    def parse (self, xml):
        xml = XMLParser.parse(self, xml)

        _, time = self.searchFirst(xml, 'timePosition')
        return qgstime.QgsTimeInstant (time)

class GMLTimePeriodParser (XMLParser):
    def parse (self, xml):
        xml = XMLParser.parse(self, xml)
        
        _, begin = self.searchFirst(xml, 'beginPosition')
        _, end = self.searchFirst(xml, 'endPosition')

        return qgstime.QgsTimePeriod(begin, end)

class GMLTimeParser (XMLParser):
    def parse (self, xml):
        xml = XMLParser.parse(self, xml)
        xml, timeType = self.searchFirst(xml, '*@type')
        
        if timeType == 'gml:TimePeriodType':
            return GMLTimePeriodParser().parse(xml)
        elif timeType == 'gml:TimeInstantType':
            return GMLTimeInstantParser().parse(xml)
        else:
            return qgstime.QgsTime()