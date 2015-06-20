# coding=utf-8
import unittest
from sos.sos import * #@UnusedWildImport

class ExceptionReportTest(unittest.TestCase):

    def setUp(self):
        """Runs before each test."""
        self.xml = 'test/exceptionreport.xml'
    
    def tearDown(self):
        """Runs after each test."""
        self.xml = ""

    def test_exceptionReport (self):
        with self.assertRaises(ExceptionReport):
            SensorObservationService ("", self.xml)