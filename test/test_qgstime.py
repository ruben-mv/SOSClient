# -*- coding: utf-8 -*-

import unittest
from sos.qgstime import QgsTime, QgsTimePeriod
from sos.xmlparser import XMLParserFactory


class QgsTimeTest(unittest.TestCase):

    def test_timeperiod(self):
        """TimePeriod"""

        self.assertEqual(QgsTimePeriod('2014-10-01T12:30:00Z',
                         '2014-12-24T22:00:00Z').primitive,
                         QgsTime.TimePeriod)
        self.assertEqual(str(QgsTimePeriod('2014-10-01T12:30:00Z',
                         '2014-12-24T22:00:00Z')),
                         '2014-10-01T12:30:00+00:00 2014-12-24T22:00:00+00:00'
                         )
        
    def test_timePeriodParser (self):
        """Time period parser"""
        
        timeParser = XMLParserFactory.getInstance ("GMLTime")()
        xml = '<om:samplingTime xmlns:om="http://www.opengis.net/om/1.0">\
                <gml:TimePeriod xmlns:gml="http://www.opengis.net/gml" xsi:type="gml:TimePeriodType" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\
                    <gml:beginPosition xmlns:gml="http://www.opengis.net/gml">2015-01-28T20:40:00.000</gml:beginPosition>\
                    <gml:endPosition xmlns:gml="http://www.opengis.net/gml">2015-01-28T20:50:00.000</gml:endPosition>\
                </gml:TimePeriod>\
            </om:samplingTime>'
            
        self.assertEqual(str(timeParser.parse(xml)), '2015-01-28T20:40:00 2015-01-28T20:50:00')
        
    def test_timeInstantParser (self):
        """Time instant parser"""
        
        timeParser = XMLParserFactory.getInstance ("GMLTime")()
        xml = '<om:samplingTime>\
                <gml:TimeInstant xsi:type="gml:TimeInstantType">\
                    <gml:timePosition>2015-03-17T17:29:00.000</gml:timePosition>\
                </gml:TimeInstant>\
            </om:samplingTime>'
            
        self.assertEqual(str(timeParser.parse(xml)), '2015-03-17T17:29:00')
        
if __name__ == "__main__":
    suite = unittest.makeSuite(QgsTimeTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
