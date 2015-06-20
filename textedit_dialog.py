# -*- coding: utf-8 -*-
'''
Created on 24 Xan, 2015

@author: ruben
'''

from PyQt4 import QtGui
from utils import WidgetFactory

class TextEditDialog (QtGui.QDialog, WidgetFactory.getClass("textedit_dialog")):
    '''
    classdocs
    '''

    def __init__(self, parent=None, text='', highlighterClass = None):
        '''
        Constructor
        '''
        super(TextEditDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        self.setupUi(self)
        
        self.txtBrowser.setPlainText (text)
        
        if highlighterClass:
            highlighterClass (self.txtBrowser)
    
    @property
    def text (self):
        try:
            return self.txtBrowser.toPlainText()
        except:
            return ''
        