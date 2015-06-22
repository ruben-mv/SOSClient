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
from utils import WidgetFactory

class TextEditDialog (QtGui.QDialog, WidgetFactory.getClass("textedit_dialog")):
    """
    Text edit dialog with format highlight
    """

    def __init__(self, parent=None, text='', highlighterClass = None):
        """Constructor
        :param parent: Parent object
        :type parent: QWidget
        :param text: Text to edit
        :type text: str
        :param highlighterClass: Syntax highlighter class 
        :type highlighterClass: QSyntaxHighlighter
        """
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
        