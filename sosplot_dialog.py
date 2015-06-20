# -*- coding: utf-8 -*-

from PyQt4 import QtGui, QtCore
from qgis.core import QgsVectorLayer, QgsFeatureRequest
from utils import WidgetFactory
from ui.utils import ComboBoxDelegate, DoubleSpinBoxDelegate, ColorButtonDelegate, SliderDelegate
from matplotlib.lines import Line2D
from matplotlib.markers import MarkerStyle
from matplotlib.colors import rgb2hex
from matplotlib import dates as mpdates
from matplotlib import rcParams, rcdefaults
import sys

maxFloat = sys.float_info.max

class SOSPlotDialog(QtGui.QDialog, WidgetFactory.getClass('sosplot_dialog')):
    def __init__(self, layer, parent=None):
        super(SOSPlotDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        self.layer = layer
        if type(self.layer) <> type (QgsVectorLayer()) :
            raise TypeError(self.tr("Selector layer isn't a vector layer"))
        #if not "type=SOS" in layer.source():
        #    raise TypeError("No es capa SOS")
        if self.layer.selectedFeatureCount() == 0:
            raise ValueError (self.tr("No features selected"))
        
        self.setupUi(self)
        
        map (lambda w: w.setRange(-maxFloat,maxFloat),[self.xMinFloat, self.xMaxFloat, self.yMinFloat, self.yMaxFloat])
        def DateTimeEdit2SpinBox (widget):
            widget.setValue = lambda value: widget.setDateTime(mpdates.num2date(value))
            widget.value = lambda: mpdates.date2num(widget.dateTime().toPyDateTime())
        map(DateTimeEdit2SpinBox, [self.xMinTime, self.xMaxTime, self.yMinTime, self.yMaxTime])
        
        request = QgsFeatureRequest()
        request.setFlags(QgsFeatureRequest.NoGeometry)
        request.setFilterFids(self.layer.selectedFeaturesIds())
        self.foiList = set([f.attribute("foi") for f in layer.getFeatures(request)])
        self.foiList = list(self.foiList)
        self.foiList.sort()
        self.plotWidget.genColorMap (len(self.foiList))
        
        self.xProperty.addItems([str(f.name()) for f in list(layer.pendingFields())[2:]])
        self.yProperty.addItems([str(f.name()) for f in list(layer.pendingFields())[2:]])
        self.xProperty.setCurrentIndex (0)
        self.yProperty.setCurrentIndex (1)
        
        self.draw()
        self.plotWidget.title = self.layer.name()
        self.plotWidget.xLabel = self.xProperty.currentText()
        self.plotWidget.yLabel = self.yProperty.currentText()
        
        self.plotWidget.picked.connect (self.dataSeriePicked)
        self.plotWidget.axisChanged.connect (self.axisLimChanged)
        
        self.title.editingFinished.connect(lambda: self.optionsToPlot(option='title'))
        self.legendChk.stateChanged.connect(lambda v: self.optionsToPlot(option='legend'))
        self.legendPos.currentIndexChanged.connect(lambda v: self.optionsToPlot(option='legend'))
        self.legendCols.valueChanged.connect(lambda v: self.optionsToPlot(option='legend'))
        self.gridChk.stateChanged.connect(lambda v: self.optionsToPlot(option='grid'))
        self.xSorted.toggled.connect(self.optionsToPlot)
        self.ySorted.toggled.connect(self.optionsToPlot)
        self.timeFormat.editingFinished.connect(self.optionsToPlot)
        
        self.xProperty.currentIndexChanged.connect(lambda v: self.optionsToPlot(option='xProperty'))
        self.xLabel.editingFinished.connect(lambda: self.optionsToPlot(option='xLabel'))
        self.xMinFloat.editingFinished.connect(lambda: self.optionsToPlot(option='xRange'))
        self.xMaxFloat.editingFinished.connect(lambda: self.optionsToPlot(option='xRange'))
        self.xMinTime.editingFinished.connect(lambda: self.optionsToPlot(option='xRange'))
        self.xMaxTime.editingFinished.connect(lambda: self.optionsToPlot(option='xRange'))
        
        self.yProperty.currentIndexChanged.connect(lambda v: self.optionsToPlot(option='yProperty'))
        self.yLabel.editingFinished.connect(lambda: self.optionsToPlot(option='yLabel'))
        self.yMinFloat.editingFinished.connect(lambda: self.optionsToPlot(option='yRange'))
        self.yMaxFloat.editingFinished.connect(lambda: self.optionsToPlot(option='yRange'))
        self.yMinTime.editingFinished.connect(lambda: self.optionsToPlot(option='yRange'))
        self.yMaxTime.editingFinished.connect(lambda: self.optionsToPlot(option='yRange'))
        
        map (lambda k: self.lineStyle.addItem(k, self.StylesTable.lineStyles[k]), sorted(self.StylesTable.lineStyles))
        map (lambda k: self.marker.addItem(k, self.StylesTable.markers[k]), sorted(self.StylesTable.markers))
        self.defaultStyle.button(QtGui.QDialogButtonBox.Reset).clicked.connect(self.restoreDefaultStyle)
        self.defaultStyle.button(QtGui.QDialogButtonBox.Apply).clicked.connect(lambda: self.optionsToPlot (option='defaultStyle'))
        map(lambda b: b.setAutoDefault(False), self.defaultStyle.buttons())
        
        self.optionsFromPlot()
        
        self.stylesTable.setItemDelegateForColumn (1, ColorButtonDelegate(self))
        self.stylesTable.setItemDelegateForColumn (2, ComboBoxDelegate(self,self.StylesTable.lineStyles))
        self.stylesTable.setItemDelegateForColumn (3, DoubleSpinBoxDelegate(self, (0,100)))
        self.stylesTable.setItemDelegateForColumn (4, ComboBoxDelegate(self,self.StylesTable.markers))
        self.stylesTable.setItemDelegateForColumn (5, DoubleSpinBoxDelegate(self, (0,100)))
        self.stylesTable.setItemDelegateForColumn (6, SliderDelegate(self, (0.0,1.0)))
    
    def optionsFromPlot (self):
        self.title.setText (self.plotWidget.title)
        self.setWindowTitle(self.plotWidget.title)
        
        self.legendChk.setChecked (self.plotWidget.legendVisible)
        self.legendPos.setCurrentIndex (self.plotWidget.legendPos) 
        self.legendCols.setValue (self.plotWidget.legendCols)
        
        self.gridChk.setChecked(self.plotWidget.gridVisible)
        
        self.xLabel.setText (self.plotWidget.xLabel)
        
        minValue, maxValue = self.plotWidget.xLim
        self.xMin.setValue (minValue)
        self.xMax.setValue (maxValue)
        
        self.yLabel.setText (self.plotWidget.yLabel)
        
        minValue, maxValue = self.plotWidget.yLim
        self.yMin.setValue (minValue)
        self.yMax.setValue (maxValue)
        
        self.styleFromPlot()
        
    def optionsToPlot (self, option=None):
        resetStyle = (option == 'defaultStyle')
        if option == None or option == 'defaultStyle':
            rcParams['lines.linewidth'] = self.lineWidth.value()
            rcParams['lines.linestyle'] = self.lineStyle.itemData(self.lineStyle.currentIndex ())
            rcParams['lines.marker'] = self.marker.itemData(self.marker.currentIndex ())
            rcParams['lines.markersize'] = self.markerSize.value()
            option = None
        if not option or option == 'xProperty' or option == 'yProperty':
            self.draw(resetStyle)
            option = None
        if not option or option == 'title':
            self.plotWidget.title = self.title.text()
            self.setWindowTitle(self.title.text())
        if not option or option == 'legend':
            self.plotWidget.legendPos = self.legendPos.currentIndex()
            self.plotWidget.legendCols = self.legendCols.value()
            self.plotWidget.legendVisible = self.legendChk.isChecked()
        if not option or option == 'grid':
            self.plotWidget.gridVisible = self.gridChk.isChecked()
        if not option or option == 'xProperty':
            self.xLabel.setText (self.xProperty.currentText())
        if not option or option == 'xLabel':
            self.plotWidget.xLabel = self.xLabel.text()
        if not option or option == 'xRange':
            self.plotWidget.xLim = (self.xMin.value(),self.xMax.value())
        if not option or option == 'yProperty':
            self.yLabel.setText (self.yProperty.currentText())
        if not option or option == 'yLabel':
            self.plotWidget.yLabel = self.yLabel.text()
        if not option or option == 'yRange':
            self.plotWidget.yLim = (self.yMin.value(),self.yMax.value())
        self.plotWidget.draw()
    
    def draw (self, resetStyle = False):
        xField = self.xProperty.currentText()
        yField = self.yProperty.currentText()
        
        #X-Axis limits
        self.xMinTime.setVisible (xField == 'Time')
        self.xMaxTime.setVisible (xField == 'Time')
        self.xMinFloat.setVisible(xField != 'Time')
        self.xMaxFloat.setVisible(xField != 'Time')
        self.xMin = self.xMinFloat if xField != 'Time' else self.xMinTime
        self.xMax = self.xMaxFloat if xField != 'Time' else self.xMaxTime
        #Y-Axis limits
        self.yMinTime.setVisible (yField == 'Time')
        self.yMaxTime.setVisible (yField == 'Time')
        self.yMinFloat.setVisible(yField != 'Time')
        self.yMaxFloat.setVisible(yField != 'Time')
        self.yMin = self.yMinFloat if yField != 'Time' else self.yMinTime
        self.yMax = self.yMaxFloat if yField != 'Time' else self.yMaxTime 
        
        ySorted = self.ySorted.isChecked()
        
        self.plotWidget.clean (xField = xField,
                               yField = yField,
                               resetStyle = resetStyle)

        request = QgsFeatureRequest ()
        request.setFlags(QgsFeatureRequest.NoGeometry)

        for foi in self.foiList:
            request.setFilterExpression("foi = '%s'" % foi)
            if ySorted:
                dataSerie = [(f.attribute(yField),f.attribute(xField)) for f in self.layer.getFeatures(request)]
            else:
                dataSerie = [(f.attribute(xField),f.attribute(yField)) for f in self.layer.getFeatures(request)]
            dataSerie.sort()
            
            if len (dataSerie):
                if ySorted:
                    y,x = map(list, zip(*dataSerie))
                else:
                    x,y = map(list, zip(*dataSerie))
                self.plotWidget.plot(x,y, f.attribute('name'))        
        self.plotWidget.applyTimeFormat (self.timeFormat.text())
        self.plotWidget.draw ()
        
        styles = self.StylesTable (self.plotWidget.ax.get_lines())
        self.stylesTable.setModel (styles)
        styles.dataChanged.connect(self.plotWidget.draw)
    
    def styleFromPlot (self):
        self.lineWidth.setValue (rcParams['lines.linewidth'])
        lineStyle = '' if rcParams['lines.linestyle'] in ['None', None, ' '] else rcParams['lines.linestyle']
        self.lineStyle.setCurrentIndex (self.lineStyle.findData (lineStyle))
        marker = '' if rcParams['lines.marker'] in ['None', None, ' '] else rcParams['lines.marker']
        self.marker.setCurrentIndex (self.marker.findData (marker))
        self.markerSize.setValue (rcParams['lines.markersize'])
                    
    def restoreDefaultStyle (self):
        rcdefaults()
        self.styleFromPlot ()
        self.optionsToPlot ('defaultStyle')
    
    @QtCore.pyqtSlot(str)
    def dataSeriePicked (self, line):
        self.stylesTable.selectRow (self.stylesTable.model().getRowNumber(line))
        
    @QtCore.pyqtSlot(tuple, tuple)
    def axisLimChanged (self, x, y):
        map (lambda w: w.blockSignals(True), [self.xMin, self.xMax, self.yMin, self.yMax])
        self.xMin.setValue(x[0])
        self.xMax.setValue(x[1])
        self.yMin.setValue(y[0])
        self.yMax.setValue(y[1])
        map (lambda w: w.blockSignals(False), [self.xMin, self.xMax, self.yMin, self.yMax])
    
    class StylesTable (QtCore.QAbstractTableModel):
        markers = {str(v) : k for k,v in filter(lambda m: not m[0] in ['None', None, ' '],MarkerStyle.markers.items())}
        lineStyles = {str(v) : v for v in filter(lambda s: not s in ['None', None, ' '],Line2D.lineStyles.keys())}
        
        def __init__(self, styleData, parent = None, *args):
            QtCore.QAbstractTableModel.__init__(self, parent, *args)
            self.styleData = styleData
            self.labels = map(lambda l: l.get_label(), self.styleData)
            def color2hex (color):
                if isinstance(color,tuple):
                    return rgb2hex(color)
                else:
                    return {'b': '#0000ff', 'g': '#00ff00','r': '#ff0000','c': '#ff00ff','m': '#ff00ff','y': '#ffff00','k': '#000000','w': '#ffffff'
                            }.get(color,str(color))
            self.dataModel = [  (self.tr('Name'),       Line2D.get_label, None), 
                                (self.tr('Color'),      lambda l: color2hex(l.get_color()), Line2D.set_color),
                                (self.tr('Line style'), lambda l: l.get_linestyle() if l.get_linestyle() != 'None' else '', Line2D.set_linestyle),
                                (self.tr('Line width'), Line2D.get_linewidth, Line2D.set_linewidth),
                                (self.tr('Marker'),     lambda l: MarkerStyle.markers[l.get_marker()], Line2D.set_marker),
                                (self.tr('Marker size'),Line2D.get_markersize, Line2D.set_markersize),
                                (self.tr('Opacity'),      lambda l: l.get_alpha() if l.get_alpha() != None else 1, lambda line, value: line.set_alpha(float(value)))
                                ]
    
        def headerData(self, col, orientation, role):
            if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
                return self.dataModel[col][0]
            return None
        
        def rowCount(self, parent):
            return len(self.styleData)
    
        def columnCount(self, parent):
            return len(self.dataModel)
    
        def data(self, index, role):
            if not index.isValid():
                return None
            
            if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
                return self.dataModel[index.column()][1](self.styleData[index.row()])
            
            return None
    
        def setData(self, index, value, role):
            if role != QtCore.Qt.EditRole:
                return False
            self.dataModel[index.column()][2](self.styleData[index.row()], value)
            self.dataChanged.emit (index, index)
            return True
         
        def flags(self, index):
            flags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
            if self.dataModel[index.column()][2] != None:
                flags |= QtCore.Qt.ItemIsEditable
            return flags
        
        def getRowNumber (self, name):
            return self.labels.index (name)