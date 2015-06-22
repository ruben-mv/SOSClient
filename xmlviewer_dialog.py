# -*- coding: utf-8 -*-
"""
@author: Rubén Mosquera Varela
@contact: ruben.mosquera.varela@gmail.com
@copyright:
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4 import QtGui
from PyQt4.QtXml import QDomDocument
from PyQt4.QtCore import QFile
from utils import WidgetFactory, XmlModel

class XmlViewerDialog (QtGui.QDialog, WidgetFactory.getClass("xmlviewer_dialog")):
    """
    Dialog for show XML as tree and as indented text with highlight
    """

    def __init__(self, parent=None, xml='', highlighterClass = None):
        '''
        Constructor
        '''
        super(XmlViewerDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        self.setupUi(self)
        
        try:
            xml.seek(0)
        except: pass
            
        doc = QDomDocument()
        (ok, errorMsg, _, _) = doc.setContent(xml, True)
        self.lblError.setVisible (not ok)
        if ok:
            self.xmlTree.setModel (XmlModel(doc, self))
            if isinstance (xml, QFile):
                xml = doc.toString(indent=4)
        else:
            xml = ""
            self.lblError.setText (errorMsg)
                
        self.xmlText.setPlainText (xml)
        
        if highlighterClass:
            highlighterClass (self.xmlText)