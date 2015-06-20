# coding=utf-8
'''
Created on 29 Dec, 2014

@author: ruben
'''
import sys
from os import listdir
import os.path
from PyQt4 import QtGui, QtCore, uic
from qgis.core import QgsMessageLog
from qgis.gui import QgsManageConnectionsDialog
from sos.qgstime import QgsTimeInstant, QgsTimePeriod
import time

DEBUG = 1
QgsDebug = lambda msg :  QgsMessageLog.logMessage(unicode(msg), "SosClient-DEBUG", QgsMessageLog.INFO) if DEBUG else lambda msg: None

FILE = __file__

class WidgetFactory () :
    _widgets = None
    __suffix = "_base.ui"

    @classmethod
    def getClass (self, widget):
        if self._widgets == None:
            self._widgets = dict()
            currentPath = os.path.dirname(FILE)
            uiPath = os.path.join(currentPath, "ui")
            uiFiles = [(fileName.rstrip(self.__suffix),os.path.join(uiPath, fileName))
                            for fileName in listdir (uiPath)
                                if os.path.isfile(os.path.join(uiPath, FILE)) and
                                not fileName.split(self.__suffix)[-1]]
            
            sys.path.append(currentPath)
            sys.path.append(uiPath)
            for className, fileName in uiFiles:
                uiClass, _ = uic.loadUiType(fileName)
                self._widgets[className] = uiClass
            sys.path.pop()
            sys.path.pop()
        try:
            return self._widgets[widget]
        except KeyError:
            raise NotImplementedError(widget + self.__suffix)

# helper for changing the cursor
def pyqtOverrideCursor(cursor):
    def decorator(func):
        def _func(*args, **kwargs):
            QtGui.QApplication.setOverrideCursor(cursor)
            try:
                return func(*args, **kwargs)
            finally:
                QtGui.QApplication.restoreOverrideCursor()
        return _func
    return decorator

#Add actions to custom context menus
def addContextMenuActions (point, widget, actions):
    menu = widget.createStandardContextMenu()
    map (menu.addAction, actions)
    menu.exec_(widget.mapToGlobal(point))

class QStringListCheckableModel(QtGui.QStringListModel):
    '''
    classdocs
    '''
    def __init__(self, options, selected = list()):
        options.sort()
        super(QtGui.QStringListModel, self).__init__(options)
        self.checkedList = [True if options[i] in selected else False for i in range(len(options))]
       
    @property
    def stringListChecked (self):
        checked = []
        for row in range (len(self.checkedList)):
            if self.checkedList[row]:
                checked.append(self.stringList()[row])
        return checked
         
    def flags(self, index):
        return QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled
    
    def data (self, index, role=QtCore.Qt.DisplayRole) :
        if role == QtCore.Qt.DisplayRole:
            return self.stringList()[index.row()]
        
        if role == QtCore.Qt.CheckStateRole:
            return QtCore.Qt.Checked if self.checkedList[index.row()] else QtCore.Qt.Unchecked
        
    def setData(self, index, value, role):
        if role == QtCore.Qt.CheckStateRole:
            self.checkedList[index.row()] = True if value == QtCore.Qt.Checked else False
            self.dataChanged.emit(index, index)
            return True
        else:
            return False
    
    def checkAll(self):
        for row in range(len(self.checkedList)):
            index = self.index(row)
            self.setData (index, QtCore.Qt.Checked, QtCore.Qt.CheckStateRole)
            self.dataChanged.emit(index,QtCore.QModelIndex())
    
    def checkNone(self):
        for row in range(len(self.checkedList)):
            index = self.index(row)
            self.setData (index, QtCore.Qt.Unchecked, QtCore.Qt.CheckStateRole)
            self.dataChanged.emit(index,QtCore.QModelIndex())
    
    def checkInvert(self):
        for row in range(len(self.checkedList)):
            index = self.index(row)
            self.setData (index, QtCore.Qt.Unchecked if self.checkedList[row] else QtCore.Qt.Checked, QtCore.Qt.CheckStateRole)
            self.dataChanged.emit(index,QtCore.QModelIndex())
            
class QgsManageConnectionsDialogSOS (QgsManageConnectionsDialog):
    def __init__(self, parent, mode, filename = ""):
        super (QgsManageConnectionsDialog, self).__init__(parent, mode, -1, filename)
        self.populateConnections()
        
    def populateConnections (self):
        return True
    
class TimeWidget (QtGui.QWidget, WidgetFactory.getClass("time_widget")):
    
    editingFinished = QtCore.pyqtSignal()
    
    def __init__(self, parent=None):
        """Constructor."""
        super(TimeWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        self.setupUi(self)
        
        self.value = QgsTimeInstant ()
        
        self._updateWidget()
        
        self.rbCustom.toggled.connect(self._changeValue)
        self.rbFirst.toggled.connect(self._changeValue)
        self.rbLatest.toggled.connect(self._changeValue)
        self.dateEdit.dateChanged.connect(self._changeValue)
        self.timeEdit.timeChanged.connect(self._changeValue)
    
    def _updateWidget (self):
        if self.value.date == 'first':
            self.rbFirst.setChecked (True)
        elif self.value.date == 'latest':
            self.rbLatest.setChecked (True)
        else:
            self.rbCustom.setChecked (True)
            self.dateEdit.setDate (self.value.date)
            self.timeEdit.setTime (self.value.time)
            
    
    def _changeValue (self):
        if self.rbFirst.isChecked():
            self.value = QgsTimeInstant('first')
        elif self.rbLatest.isChecked():
            self.value = QgsTimeInstant('latest')
        else:
            self.value = QgsTimeInstant(QtCore.QDateTime (self.dateEdit.date(),self.timeEdit.time()).toString("yyyy-MM-dd hh:mm"))
        self.editingFinished.emit()
                
    def text(self):
        return str(self.value)
    
    def setText (self, text):
        self.value = QgsTimeInstant (text)
        self._updateWidget()
        
class TimePeriodWidget (QtGui.QWidget, WidgetFactory.getClass("timeperiod_widget")):
    
    editingFinished = QtCore.pyqtSignal()
    
    def __init__(self, parent=None):
        """Constructor."""
        super(TimePeriodWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        self.setupUi(self)
        
        self.value = QgsTimePeriod ()
        
        self._updateWidget()
        
        self.rbCustomBegin.toggled.connect(self._changeValue)
        self.dateEditBegin.dateChanged.connect(self._changeValue)
        self.timeEditBegin.timeChanged.connect(self._changeValue)
        self.rbFirstBegin.toggled.connect(self._changeValue)
        
        self.rbCustomEnd.toggled.connect(self._changeValue)
        self.dateEditEnd.dateChanged.connect(self._changeValue)
        self.timeEditEnd.timeChanged.connect(self._changeValue)
        self.rbLatestEnd.toggled.connect(self._changeValue)
    
    def _updateWidget (self):
        if self.value.beginDate == 'first':
            self.rbFirstBegin.setChecked (True)
        else:
            self.rbCustomBegin.setChecked (True)
            self.dateEditBegin.setDate (self.value.beginDate)
            self.timeEditBegin.setTime (self.value.beginTime)
            
        if self.value.endDate == 'latest':
            self.rbLatestEnd.setChecked (True)
        else:
            self.rbCustomEnd.setChecked (True)
            self.dateEditEnd.setDate (self.value.endDate)
            self.timeEditEnd.setTime (self.value.endTime)
            
    def _changeValue (self):
        if self.rbFirstBegin.isChecked():
            begin = 'first'
        else:
            begin = QtCore.QDateTime (self.dateEditBegin.date(),self.timeEditBegin.time()).toString("yyyy-MM-dd hh:mm")
        
        if self.rbLatestEnd.isChecked():
            end = 'latest'
        else:
            end = QtCore.QDateTime (self.dateEditEnd.date(),self.timeEditEnd.time()).toString("yyyy-MM-dd hh:mm")
        
        self.value = QgsTimePeriod (begin, end)
        
        self.editingFinished.emit()
                
    def text(self):
        return str(self.value)
    
    def setText (self, text):
        self.value = QgsTimePeriod (text.split()[0], text.split()[-1])
        self._updateWidget()
        
class QLineEditButton (QtGui.QLineEdit):
    
    buttonClicked = QtCore.pyqtSignal()
    
    def __init__(self,parent=None, icon = QtGui.QIcon()):
        super(QLineEditButton, self).__init__(parent)

        self.button = QtGui.QToolButton(self)
        self.button.setCursor(QtCore.Qt.ArrowCursor)

        self.button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.button.setIcon(icon)
        self.button.setStyleSheet("background: transparent; border: none;")

        layout = QtGui.QHBoxLayout(self)
        layout.setSpacing(0)
        layout.setMargin(2)
        layout.addWidget(self.button,0,QtCore.Qt.AlignRight)
        
        self.button.clicked.connect(self.buttonClicked.emit)
        
class XmlModel(QtCore.QAbstractItemModel):
    class XmlItem(object):
        def __init__(self, node, row, parent=None):
            self.domNode = node
            self.rowNumber = row
            self.parentItem = parent
            self.childItems = {}
    
        def node(self):
            return self.domNode
    
        def parent(self):
            return self.parentItem
    
        def child(self, i):
            if i in self.childItems:
                return self.childItems[i]
    
            attributesCount = self.domNode.attributes().count()
            childNodesCount = self.domNode.childNodes().count()
            if i >= 0 and i < (attributesCount + childNodesCount):
                if i < attributesCount:
                    childNode = self.domNode.attributes().item(i)
                    childItem = XmlModel.XmlItem (childNode, i, self)
                    self.childItems[i] = childItem
                    return childItem
                else:    
                        childNode = self.domNode.childNodes().item(i-attributesCount)
                        childItem = XmlModel.XmlItem(childNode, i, self)
                        self.childItems[i] = childItem
                        return childItem
        
                return None
        
        def row(self):
            return self.rowNumber
        
    def __init__(self, document, parent=None):
        super(XmlModel, self).__init__(parent)
        self.domDocument = document
        self.rootItem = XmlModel.XmlItem(self.domDocument, 0)

    def columnCount(self, parent):
        return 2

    def data(self, index, role):
        if not index.isValid():
            return None

        if role != QtCore.Qt.DisplayRole:
            return None

        item = index.internalPointer()
        node = item.node()

        if index.column() == 0:
#             if index.row() < node.parentNode().attributes().count():
#                 return '@' + node.nodeName()
#             else:
#                 return node.nodeName()
            return unicode(node.nodeName())

        if index.column() == 1:
            return unicode (node.nodeValue()) if node.nodeValue() else '' #TODO º se ve mal
            #return ' '.join(unicode(node.nodeValue()).split('\n')) if node.nodeValue() else ''

        return None

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable if index.isValid() else QtCore.Qt.NoItemFlags

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            if section == 0:
                return self.tr("Name")
            if section == 1:
                return self.tr("Value")
        return None

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        parentItem = parent.internalPointer() if parent.isValid() else self.rootItem
        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def parent(self, child):
        if not child.isValid():
            return QtCore.QModelIndex()

        childItem = child.internalPointer()
        parentItem = childItem.parent()

        if not parentItem or parentItem == self.rootItem:
            return QtCore.QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0
        
        parentItem = parent.internalPointer() if parent.isValid() else self.rootItem

        if parentItem.node().isAttr ():
            return 0
        return parentItem.node().attributes().count() + parentItem.node().childNodes().count()

class Timer (object):
    def __init__(self, text=''):
        self.verbose = len(text) > 0
        self.text = text if len(text) else 'Timer:'

    def __enter__(self):
        self.start = time.time()
        return self

    def __str__(self):
        return self.text + ' %f ms' % self.msecs
    
    def __exit__(self, *args):
        self.end = time.time()
        self.secs = self.end - self.start
        self.msecs = self.secs * 1000  # millisecs
        if self.verbose:
            print str(self)