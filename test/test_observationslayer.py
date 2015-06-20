# -*- coding: utf-8 -*-
'''
Created on 28 Feb, 2015

@author: ruben
'''

import unittest
from PyQt4.QtCore import Qt #@UnusedImport
from sos.sos import * #@UnusedWildImport


class ObservationsLayerTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.observationFiles = {}
        
        cls.observationFiles ['observationsMeteogalicia.xml'] = 'test/observationsMeteogalicia.xml'
        cls.observationFiles ['observationsIntecmar.xml'] = 'test/observationsIntecmar.xml'
        cls.observationFiles ['measurementsIntecmar.xml'] = 'test/measurementsIntecmar.xml'

    @classmethod
    def tearDownClass(cls):
        del cls.observationFiles
        
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_observationsMeteogalicia (self):
        layer = ObservationsLayer ('observationsMeteogalicia.xml', self.observationFiles ['observationsMeteogalicia.xml'])
        layer.toVectorLayer()
        
        self.assertEqual (layer.name, 'observationsMeteogalicia.xml')
        self.assertEqual (unicode(layer), u";meteoroloxicas_Vilela-A_10500: 2015-01-28T20:40:00-{u'tmin': '7.06'},")
        self.assertEqual (",".join([str(f.name()) for f in layer.provider.fields]), "foi,name,Time,tmin")
        self.assertEqual (str(layer.provider.fields[3].typeName()), "ºC")
        feature = layer.provider.getFeatures().next()
        self.assertEqual (feature.attribute("name"),"Vilela-A")
        self.assertEqual (feature.attribute("Time"), "2015-01-28T20:40:00")
        self.assertEqual (float(feature.attribute("tmin")), 7.06)
        #self.assertEqual(layer.toVectorLayer(), "")
        
    def test_observationsIntecmar (self):
        layer = ObservationsLayer ('observationsIntecmar.xml', self.observationFiles ['observationsIntecmar.xml'])
        layer.toVectorLayer()
        
        self.assertEqual (layer.name, 'observationsIntecmar.xml')
        self.assertEqual ((unicode(layer)).split(";")[1], "ctd_Liméns_1: 2015-01-13T09:29:00-{u'Temperatura': '12.6525', u'Salinidade': '35.2642'},2015-01-20T09:23:00-{u'Temperatura': '11.4385', u'Salinidade': '33.6147'},")
        self.assertEqual (",".join([str(f.name()) for f in layer.provider.fields]), "foi,name,Time,Salinidade,Temperatura")
        self.assertEqual (layer.vectorLayer.name(), layer.name)
        
    def test_measurementsIntecmar (self):
        layer = ObservationsLayer ('measurementsIntecmar.xml', self.observationFiles ['measurementsIntecmar.xml'])
        layer.toVectorLayer()
         
        self.assertEqual (layer.name, 'measurementsIntecmar.xml')
        self.assertEqual (",".join([str(f.name()) for f in layer.provider.fields]), "foi,name,Time,Temperatura,Salinidade,Profundidade")
        self.assertEqual ((unicode(layer)).split(";")[1], u"(u'ctd_Ares_42', u'10.617'): 2015-04-20T09:14:00-{u'Temperatura': '13.449999809265137', u'Salinidade': '35.344398498535156', u'Profundidade': '10.616999626159668'},")
        self.assertEqual (layer.vectorLayer.name(), layer.name)

if __name__ == "__main__":
    suite = unittest.makeSuite(ObservationsLayerTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)