# -*- coding: utf-8 -*-
'''
Created on 25 Abr, 2015

@author: ruben
'''

from PyQt4 import QtGui
from PyQt4.QtXml import QDomDocument
from PyQt4.QtCore import QFile
from utils import WidgetFactory, XmlModel

class XmlViewerDialog (QtGui.QDialog, WidgetFactory.getClass("xmlviewer_dialog")):
    '''
    classdocs
    '''

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