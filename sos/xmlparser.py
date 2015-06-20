# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Base class and factory to XML parsers
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
from PyQt4.QtXml import QDomDocument, QDomNode, QDomElement

__all__ = ['XMLParserFactory', 'XMLParser']

class XMLParserFactory () :
    _parsers = None

    @classmethod
    def getInstance (self, tagname, preffix=""):
        if self._parsers == None:
            self._parsers = dict()
            for cls in XMLParser.__subclasses__():
                self._parsers[cls.__name__] = cls
        tagname = preffix + tagname + "Parser"
        try:
            return self._parsers[tagname]
        except KeyError:
            raise NotImplementedError(tagname)

class XMLParser (object):
    __metadata__ = abc.ABCMeta

    @abc.abstractmethod
    def parse (self, xml=None):
        if isinstance (xml, QDomElement):
            return xml
        
        doc = QDomDocument()
        (ok, errorMsg, errorLine, errorCol) = doc.setContent(xml, True)
        if ok:
            return doc.documentElement()
        else:
            raise ValueError ("{} in line {}, column {}".format(errorMsg, errorLine, errorCol))
    
    @staticmethod
    def searchFirst (xml, query):
        for node, value in XMLParser.search (xml, query):
            return node, value
        return None, None

    @staticmethod
    def search (xml, query):
        def _text (node, attr=None):
            if attr:
                return unicode (node.attribute(attr))
            if node.firstChild().isText():
                return unicode (node.firstChild().nodeValue())
            return unicode (node.localName())
            
        if not isinstance (xml, QDomNode):
                    raise TypeError ("xml must be a QDomNode")
        if not isinstance (query, str):
            raise TypeError ("query must be a string")

        tag = query.split("@")[ 0]
        attr = query.split("@")[-1] if "@" in query else ""
        val = attr.split ("=")[-1] if "=" in attr else ""
        attr = attr.split ("=")[ 0]

        for tag in tag.split("/"):
            if   tag == "*": xml = xml.firstChildElement ()         
            elif tag <> "":  xml = xml.firstChildElement (tag)

        while not xml.isNull():
            if attr <> "":
                if val == "":
                    yield xml, _text(xml, attr)
                elif val == xml.attribute(attr):
                    yield xml, _text(xml)
            else:
                yield xml, _text(xml)
            xml = xml.nextSiblingElement (tag if tag <> "*" else "")
