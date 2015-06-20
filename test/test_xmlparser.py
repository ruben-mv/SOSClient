# -*- coding: utf-8 -*-

import unittest
from sos.xmlparser import XMLParser


class XMLParserTest(unittest.TestCase):

    """Test xml parser works."""

    XMLDATA = \
        """<?xml version='1.0' encoding='UTF-8'?>
<root v='2'>
  <node id='1'>Node 1</node>
  <node id='2'>Node 2</node>
  <node id='3'>Node 3</node>
  <subnodes ref='1'>
    <subnode>S1.1</subnode>
    <subnode>S1.2</subnode>
  </subnodes>
  <subnodes ref='2'>
    <subnode>S2.1</subnode>
    <subnode>S2.2</subnode>
  </subnodes>
  <vacio/>
  <siguiente/>
</root>"""

    def setUp(self):
        """Runs before each test."""

        self.parser = XMLParser()
        self.xml = self.parser.parse(self.XMLDATA)

    def tearDown(self):
        """Runs after each test."""

        self.parser = None
        self.xml = None

    def test_search_attribute(self):
        """Test buscar atributo"""

        (_, value) = self.parser.searchFirst(self.xml, '@v')
        self.assertEqual(value, '2')

    def test_search_subnode(self):
        """Test buscar subnodos"""

        lista = []
        for (_, value) in self.parser.search(self.xml, 'node'):
            lista.append(value)
        self.assertEqual(lista, ['Node 1', 'Node 2', 'Node 3'])

    def test_search_subnode_attribute(self):
        """Test buscar atributos en subnodos"""

        lista = []
        for (_, value) in self.parser.search(self.xml, 'node@id'):
            lista.append(value)
        self.assertEqual(lista, ['1', '2', '3'])

    def test_search_subnode_value(self):
        """Test buscar subnodo 3"""

        lista = []
        for (node, value) in self.parser.search(self.xml, 'node@id=3'):
            self.assertEqual(node.attribute('id'), '3')
            lista.append(value)
        self.assertEqual(lista, ['Node 3'])
        self.assertEqual(self.parser.searchFirst(self.xml, 'node@id=3'
                         )[1], 'Node 3')

    def test_search_subnode_2_value(self):
        """Test buscar subnodos 2do nivel"""

        lista = []
        for (n, _) in self.parser.search(self.xml, 'subnodes@ref=2'):
            for (_, v2) in self.parser.search(n, 'subnode'):
                lista.append(v2)
        self.assertEqual(lista, ['S2.1', 'S2.2'])
