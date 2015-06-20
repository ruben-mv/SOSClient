from PyQt4 import QtGui, QtCore
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib import dates as mpdates
from matplotlib import rcParams, rcdefaults
from matplotlib.cm import get_cmap
from random import randint

class QDirChooser (QtGui.QLineEdit):
    def __init__(self,parent=None, dirName = QtCore.QDir.tempPath()):
        super(QDirChooser, self).__init__(parent)

        self.setText(dirName)
        self.button = QtGui.QToolButton(self)
        self.button.setText("...")
        self.setReadOnly(True)

        layout = QtGui.QHBoxLayout(self)
        layout.setSpacing(0)
        layout.setMargin(0)
        layout.addWidget(self.button,0,QtCore.Qt.AlignRight)
        
        self.button.clicked.connect(self._buttonClicked)
    
    def _buttonClicked (self):
        dirName = QtGui.QFileDialog.getExistingDirectory(self, "", self.text())
        if len(dirName):
            self.setText (dirName)
            
class QMplWidget (QtGui.QWidget):
    
    picked = QtCore.pyqtSignal (str)
    axisChanged = QtCore.pyqtSignal (tuple, tuple)
    
    def __init__(self, parent=None):
        super(QMplWidget, self).__init__(parent)
        
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        try:
            self.ax = self.figure.add_subplot(111)
        except:
            rcdefaults()
            self.ax = self.figure.add_subplot(111)
        
        
        self.toolbar = NavigationToolbar(self.canvas, self)
        map (lambda a: a.setVisible(False), filter(lambda a: a.text() in ['Customize'], self.toolbar.findChildren(QtGui.QAction)))

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.addWidget(self.toolbar)
        self.setLayout(layout)
        
        def on_pick(event):
            if event.mouseevent.button == 1:
                label = event.artist.get_label()
                if len(label):
                    self.picked.emit (label)
        self.canvas.mpl_connect('pick_event', on_pick)
        
        self.legendCols = 1
        self.legendPos = 0
        
        self.grid = rcParams['axes.grid']
        self.qualifiedColorMaps = ['Accent', 'Dark2', 'Paired', 'Pastel1', 'Pastel2', 'Set1', 'Set2', 'Set3']
        self.colorMap = None
        
        self.oldLines = {}
        self.xdate = False
        self.ydate = False
        self.clean()
        
    def genColorMap (self, numColors=10, colorMapName = ''):
        if not colorMapName in self.qualifiedColorMaps:
            colorMapName = self.qualifiedColorMaps[randint(1,len(self.qualifiedColorMaps))-1] 
        cm = get_cmap(colorMapName, numColors)
        self.colorMap = [cm(1.*i/numColors) for i in range(numColors)]
    
    def clean (self, xField='', yField='', resetStyle = False):
        self.oldLines = {}
        if not resetStyle:
            map (lambda l: self.oldLines.__setitem__(l.get_label(),l), self.ax.get_lines())
        
        self.ax.cla()        
        def on_axeslim_changed (ax):
            self.axisChanged.emit (ax.get_xlim(),ax.get_ylim())
        self.ax.callbacks.connect('xlim_changed', on_axeslim_changed)
        self.ax.callbacks.connect('ylim_changed', on_axeslim_changed)
        on_axeslim_changed (self.ax)
        
        self.xdate = (xField == 'Time')
        self.ydate = (yField == 'Time')
        self.ax.set_color_cycle(self.colorMap)
    
    def applyTimeFormat (self, timeFormat = ''):
        timeFormatter = mpdates.DateFormatter(timeFormat) if len(timeFormat) else None
        if self.xdate and timeFormatter:
            self.ax.xaxis.set_major_formatter(timeFormatter)
        if self.ydate and timeFormatter:
            self.ax.yaxis.set_major_formatter(timeFormatter)
        self.figure.autofmt_xdate()
            
    def plot(self, x=[], y=[], label = None):
        if self.xdate:
            x = [mpdates.datestr2num(v) for v in x]
        if self.ydate:
            y = [mpdates.datestr2num(v) for v in y]
        
#         line, = self.ax.plot_date (x, y, label = label,
#                                    xdate=self.xdate, ydate=self.ydate,
#                                    picker=5,
#                                    fmt='')
        line, = self.ax.plot (x, y, label = label,
                                   picker=5)
        if self.xdate:
            self.ax.xaxis_date()
        if self.ydate:
            self.ax.yaxis_date()
            
        if self.oldLines.has_key(label):
            line.update_from(self.oldLines.pop(label))
        
    def updateLegend (self):
        self.ax.legend(loc = self.legendPos, ncol = self.legendCols)
        legend = self.ax.get_legend()
        if legend:
            legend.draggable (True)

    @property
    def xLim (self):
        return self.ax.get_xlim()
    
    @xLim.setter
    def xLim (self, xRange):
        self.ax.set_xlim (xRange)
    
    @property
    def yLim (self):
        return self.ax.get_ylim()
    
    @yLim.setter
    def yLim (self, yRange):
        self.ax.set_ylim (yRange)
    
    @property
    def title (self):
        return self.ax.get_title()
        
    @title.setter        
    def title (self, value):
        self.ax.set_title (value, weight='bold')
    
    @property
    def xLabel (self):
        return self.ax.get_xlabel()
    
    @xLabel.setter
    def xLabel (self, value):
        self.ax.set_xlabel (value)
        
    @property
    def yLabel (self):
        return self.ax.get_ylabel()
    
    @yLabel.setter
    def yLabel (self, value):
        self.ax.set_ylabel (value)
        
    @property
    def legendVisible (self):
        return self.ax.get_legend().get_visible() if self.ax.get_legend() else False
        
    @legendVisible.setter        
    def legendVisible (self, value):
        if value:
            self.updateLegend ()
        try:
            self.ax.get_legend().set_visible (value)
        except: pass
    
    @property
    def gridVisible (self):
        return self.grid
    
    @gridVisible.setter
    def gridVisible (self, value):
        self.grid = value
        self.ax.grid(self.grid)
    
    def draw (self):        
        self.canvas.draw()
        self.axisChanged.emit (self.ax.get_xlim(),self.ax.get_ylim())
        
class DoubleSpinBoxDelegate(QtGui.QItemDelegate):
    def __init__ (self, parent, valueRange = (0.0,1.0)):
        super (DoubleSpinBoxDelegate, self).__init__(parent)
        self.valueRange = valueRange
        self.step = min((valueRange[1]-valueRange[0])/10,1.0)
            
    def createEditor(self, parent, option, index):
        editor = QtGui.QDoubleSpinBox(parent)
        editor.setRange(self.valueRange[0],self.valueRange[1])
        editor.setSingleStep (self.step)
        return editor

    def setEditorData(self, spinBox, index):
        value = index.model().data(index, QtCore.Qt.EditRole)
        spinBox.setValue(value)

    def setModelData(self, spinBox, model, index):
        spinBox.interpretText()
        value = spinBox.value()
        model.setData(index, value, QtCore.Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)
        
class ComboBoxDelegate(QtGui.QItemDelegate):
    def __init__ (self, parent, items = {}):
        super (ComboBoxDelegate, self).__init__(parent)
        if isinstance(items, list):
            self.items = dict(zip(items,items))
        else:
            self.items = items
        
    def createEditor(self, parent, option, index):
        editor = QtGui.QComboBox(parent)
        map (lambda k: editor.addItem(k, self.items[k]), sorted(self.items))
        return editor

    def setEditorData(self, comboBox, index):
        value = index.model().data(index, QtCore.Qt.EditRole)
        comboBox.setCurrentIndex (comboBox.findText (value))

    def setModelData(self, comboBox, model, index):
        value = comboBox.itemData(comboBox.currentIndex ())
        model.setData(index, value, QtCore.Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)
        
class ColorButtonDelegate(QtGui.QItemDelegate):
    def __init__(self, parent=None):
        super(ColorButtonDelegate, self).__init__(parent)

    def createEditor(self, parent, option, index):
        colorDialog = QtGui.QColorDialog(self.parent())
        colorDialog.setProperty('accepted', False)
        return colorDialog
 
    def setEditorData(self, colorDialog, index):
        value = index.model().data(index, QtCore.Qt.EditRole)
        colorDialog.setCurrentColor(QtGui.QColor(value))
 
    def setModelData(self, colorDialog, model, index):
        value = colorDialog.currentColor().name()
        colorDialog.accepted.connect (lambda: model.setData(index, value, QtCore.Qt.EditRole))

    def paint (self, painter, option, index):
        value = index.model().data(index, QtCore.Qt.EditRole)
        painter.fillRect (option.rect, QtGui.QColor(value))

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)
        
class SliderDelegate(QtGui.QItemDelegate):
    def __init__ (self, parent, valueRange = (0.0,1.0)):
        super (SliderDelegate, self).__init__(parent)
        self.sliderValue = lambda v: int(round(abs((v - valueRange[0])/(valueRange[1]-valueRange[0]) * 100)))
        self.realValue = lambda v: round(valueRange[0] + (valueRange[1]-valueRange[0])*v/100,2)
            
    def createEditor(self, parent, option, index):
        editor = QtGui.QSlider (QtCore.Qt.Horizontal,parent)
        editor.setRange(0,100)
        editor.setSingleStep (5)
        return editor

    def setEditorData(self, slider, index):
        value = self.sliderValue(index.model().data(index, QtCore.Qt.EditRole))
        slider.setValue(value)

    def setModelData(self, slider, model, index):
        value = self.realValue(slider.value())
        model.setData(index, value, QtCore.Qt.EditRole)

    def paint (self, painter, option, index):
        percent = self.sliderValue(index.model().data(index, QtCore.Qt.EditRole))
        styleOption = QtGui.QStyleOptionProgressBar()
        styleOption.rect = option.rect
        styleOption.minimum = 1
        styleOption.maximum = 100
        styleOption.progress = percent
        styleOption.textVisible = True
        styleOption.text = "%d%%" %  percent
        QtGui.QApplication.style().drawControl( QtGui.QStyle.CE_ProgressBar, styleOption, painter )
        
    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)
