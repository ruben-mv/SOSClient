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

from PyQt4 import QtGui, QtCore

class XmlHighlighter(QtGui.QSyntaxHighlighter):
    """
    XML syntax highlight
    """
    
    def __init__(self, doc):
        '''
        Constructor
        '''
        def _format (color, style=''):
            """Return a QTextCharFormat with the given attributes."""
            _format = QtGui.QTextCharFormat()
            if color != '':
                _format.setForeground(getattr(QtCore.Qt, color))
            if 'bold' in style:
                _format.setFontWeight(QtGui.QFont.Bold)
            if 'italic' in style:
                _format.setFontItalic(True)
            return _format
        
        super (XmlHighlighter, self).__init__(doc)
        
        self.styles = {'special'    : _format ('darkBlue', 'bold'),
                       'keyword'    : _format ('darkBlue'),
                       'attribute'  : _format ('darkGreen'),
                       'comment'    : _format ('lightGray', 'italic'),
                       'string'     : _format ('darkMagenta'),
                       'numbers'    : _format ('red'),
                       'values'     : _format ('black', 'bold')
                       }
        
        self.rules = [(self.styles['values']    , QtCore.QRegExp(".")),
                      (self.styles['numbers']   , QtCore.QRegExp(">[\+\-0-9,\\. ]+<")),
                      (self.styles['keyword']   , QtCore.QRegExp("<[a-zA-Z_:]+(>|\\b)")),
                      (self.styles['keyword']   , QtCore.QRegExp(">")),
                      (self.styles['keyword']   , QtCore.QRegExp("/>")),
                      (self.styles['keyword']   , QtCore.QRegExp("</[a-zA-Z_:]+>")),
                      (self.styles['special']   , QtCore.QRegExp("<\\?xml\\b")),
                      (self.styles['special']   , QtCore.QRegExp("\\?>")),
                      (self.styles['attribute'] , QtCore.QRegExp(" [a-zA-Z:]+=")),
                      (self.styles['string']    , QtCore.QRegExp("\"[^\"]*\"")),
                      (self.styles['string']    , QtCore.QRegExp("'[^']*'"), ),
                      (self.styles['comment']   , QtCore.QRegExp("<!--[^>]*-->"))
                      ]
        #self.rules = [(self.styles['namespace'] , QtCore.QRegExp("<[a-zA-Z]:"))]
        
    def highlightBlock(self, text):
        """Highlight a text block."""
        for format_, expression in self.rules:
            # get first match
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format_)
                # jump to next match
                index = expression.indexIn(text, index + length)
        self.setCurrentBlockState(0)