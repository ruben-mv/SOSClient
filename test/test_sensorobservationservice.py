# coding=utf-8
import unittest
from qgis.core import QgsRectangle
from sos.qgstime import QgsTime
from sos.sos import * #@UnusedWildImport

class SensorObservationServiceTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.service = SensorObservationService ("test/capabilities52N.xml", "test/capabilities52N.xml")

    @classmethod
    def tearDownClass(cls):
        cls.service = None

    def setUp(self):
        """Runs before each test."""
        pass
    
    def tearDown(self):
        """Runs after each test."""
        pass

    def test_version_1 (self):
        """Version 1"""
        self.assertEqual(self.service.capabilitiesVersion, "1.0.0")

    def test_serviceIdentification (self):
        """Service Identification"""
        self.assertEqual(self.service.identification.title, "IFGI SOS")
        self.assertEqual(self.service.identification.abstract, "52n SOS at IFGI, Muenster, Germany, SVN: ${buildNumber} @ ${timestamp}")
        self.assertEqual(self.service.identification.keywords, ["water level, gauge height, waterspeed"])
        self.assertEqual(self.service.identification.serviceType, "OGC:SOS")
        self.assertEqual(self.service.identification.serviceTypeVersion, "1.0.0")

    def test_serviceProvider (self):
        """Service Provider"""
        self.assertEqual(self.service.provider.providerName, "52North")
        self.assertEqual(self.service.provider.providerSite, "http://52north.org/swe")
        self.assertEqual(self.service.provider.phones, {'Voice' : '+49(0)251/396 371-0'})
        self.assertEqual(self.service.provider.address, {"DeliveryPoint" : "Marin-Luther-King-Weg 24",
                                "City" : "Muenster",
                                "AdministrativeArea" : "North Rhine-Westphalia",
                                "PostalCode" : "48155",
                                "Country" : "Germany",
                                "ElectronicMailAddress" : "info@52north.org"})

    def test_serviceOffertingsList (self):
        """Offerings list"""
        with self.assertRaises(KeyError):
            self.service[None]
    
        self.assertEqual(self.service.observationOfferingList, ['GAUGE_HEIGHT', 'WATER_SPEED', 'TEMPERATURE', 'CHOIVA_VENTO'])
        for ID in self.service.observationOfferingList:
            self.assertEqual (ID, self.service[ID].id)

    def test_serviceOffertingCHOIVA_VENTO (self):
        """Offerings CHOIVA_VENTO"""
        self.assertEqual(self.service['CHOIVA_VENTO'].name, "A choiva, balances hidricos e velocidade do vento en Galicia")
        self.assertEqual(self.service['CHOIVA_VENTO'].description, None)
        self.assertEqual(self.service['CHOIVA_VENTO'].srsName, "urn:ogc:def:crs:EPSG:4326")
        self.assertIsInstance(self.service['CHOIVA_VENTO'].boundedBy, QgsRectangle)
        self.assertIsInstance(self.service['CHOIVA_VENTO'].time, QgsTime)
        self.assertGreater(len(self.service['CHOIVA_VENTO'].proceduresList), 0)
        self.assertGreater(len(self.service['CHOIVA_VENTO'].observedPropertiesList), 0)
        self.assertEqual(self.service['CHOIVA_VENTO'].responseFormat, 'text/xml;subtype="om/1.0.0"')
        self.assertEqual(self.service['CHOIVA_VENTO'].resultModel, ['ns:Measurement', 'ns:Observation'])
        self.assertEqual(self.service['CHOIVA_VENTO'].responseMode, "inline")
        
    def test_operationsMetadata (self):
        """ Operations Metadata"""
        self.assertEqual (self.service.operationsMetadata.keys(), ['GetCapabilities','GetFeatureOfInterest','DescribeSensor','GetObservation','GetObservationById'])
        self.assertEqual (self.service.operationsMetadata['GetCapabilities'].parameters['service'], ['SOS'])
        
    def test_filterCapabilities (self):
        """ Filter capabilities """
        self.assertIn("gml:Envelope", self.service.spatialOperands)
        self.assertIn("BBOX", self.service.spatialOperators)
        self.assertIn("gml:TimePeriod", self.service.temporalOperands)
        self.assertIn("TM_After", self.service.temporalOperators)
        self.assertIn("EqualTo", self.service.scalarOperators)
        
if __name__ == "__main__":
    suite = unittest.makeSuite(SensorObservationServiceTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
