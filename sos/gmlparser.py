# -*- coding: utf-8 -*-
"""
This module includes GML...Parser classes.
"""

from xmlparser import XMLParser
import qgstime

class GMLTimeInstantParser (XMLParser):
    """
    Parse an xml node to extract timePosition as QgsTimeInstant
    """
    def parse (self, xml):
        xml = XMLParser.parse(self, xml)

        _, time = self.searchFirst(xml, 'timePosition')
        return qgstime.QgsTimeInstant (time)

class GMLTimePeriodParser (XMLParser):
    """
    Parse an xml node to extract beginPosition and endPosition as QgsTimePeriod
    """
    def parse (self, xml):
        xml = XMLParser.parse(self, xml)
        
        _, begin = self.searchFirst(xml, 'beginPosition')
        _, end = self.searchFirst(xml, 'endPosition')

        return qgstime.QgsTimePeriod(begin, end)

class GMLTimeParser (XMLParser):
    """
    Parse an xml node to extract type and process it with correct parser
    """
    def parse (self, xml):
        xml = XMLParser.parse(self, xml)
        timeNode, timeType = self.searchFirst(xml, '*@type')
        
        if not timeType:
            timeNode, _ = self.searchFirst(xml, '*@id')
            timeType = 'gml:' + timeNode.tagName() + 'Type'
        
        if timeType == 'gml:TimePeriodType':
            return GMLTimePeriodParser().parse(timeNode)
        elif timeType == 'gml:TimeInstantType':
            return GMLTimeInstantParser().parse(timeNode)
        else:
            return qgstime.QgsTime()