# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SOSClientDialog
                                 A QGIS plugin
 OGC Sensor Observation Sensor Client
                             -------------------
        begin                : 2014-11-26
        git sha              : $Format:%H$
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

from PyQt4 import QtGui, QtCore
from PyQt4.QtNetwork import QNetworkRequest, QNetworkReply
from qgis.core import QgsApplication, QgsOWSConnection, QgsNetworkAccessManager, QgsMessageLog, QgsMapLayerRegistry
from qgis.gui import QgsNewHttpConnection, QgsMessageBar
from qgis.utils import showPluginHelp
from sos.sos import SensorObservationService, FilterRequest, ObservationsLayer
from utils import WidgetFactory, QStringListCheckableModel, QgsDebug, TimeWidget, TimePeriodWidget, QLineEditButton, addContextMenuActions#, QgsManageConnectionsDialogSOS
from qgsmaptool_capturespatialoperand import QgsMapToolCaptureSpatialOperand
from textedit_dialog import TextEditDialog
from xmlviewer_dialog import XmlViewerDialog
from xmlhighlighter import XmlHighlighter
from tempfile import mkstemp
import os

class SOSClientDialog(QtGui.QDialog, WidgetFactory.getClass('sos_client_dialog')):
    def __init__(self, parent=None, iface = None):
        """Constructor."""
        super(SOSClientDialog, self).__init__(parent)
        
        settings = QtCore.QSettings ()
                
        self.iface = iface
        self.reply = None
        self.service = None
        self.filterRequest = None
        self.createTimeManagerLayer = False
        self.addLayerToTimeManager = lambda *a,**k: None
        
        # Set up the user interface from Designer.
        self.setupUi(self)
        
        #Ayuda
        self.btnBox.helpRequested.connect(lambda: showPluginHelp(filename="help/index"))
        # Botón Añadir y Editar y añadir
        self.btnAdd.setDefaultAction (self.actionAdd)
        self.btnAdd.addAction(self.actionEditRequest)
        self.btnBox.addButton(self.btnAdd, QtGui.QDialogButtonBox.ActionRole)
        self.btnAdd.setEnabled(False)
        
        #Guardar y cargar lista de servidores
        self.btnSave.setVisible (False)
        self.btnLoad.setVisible (False)

        #Visor de información del servidor
        self.htmlView.document().setDefaultStyleSheet(QgsApplication.reportStyleSheet())
        self.htmlView.customContextMenuRequested.connect (lambda point, widget=self.htmlView, actions = [self.actionShowXML]: addContextMenuActions (point,widget, actions))
        
        #Acciones de selección para listas
        self.lstProperties.addAction(self.actionSelectAllProperties)
        self.lstProperties.addAction(self.actionSelectNoneProperties)
        self.lstProperties.addAction(self.actionSelectInvertProperties)
        self.lstFeatures.addAction(self.actionSelectAllFeatures)
        self.lstFeatures.addAction(self.actionSelectNoneFeatures)
        self.lstFeatures.addAction(self.actionSelectInvertFeatures)
        self.lstProcedures.addAction(self.actionSelectAllProcedures)
        self.lstProcedures.addAction(self.actionSelectNoneProcedures)
        self.lstProcedures.addAction(self.actionSelectInvertProcedures)

        #Filtros
        self.grpFilterSpatial.setEnabled (False)
        self.lblSpatialFilterWarning.setVisible (False)
        self.grpFilterTemporal.setEnabled (False)
        self.grpFilterScalar.setEnabled (False)
        
        #Listar conexiones
        self.populateConnectionList ()
        
        #Directorio de trabajo
        self.workDirName.setText(settings.value("SOSClient/workDir", QtCore.QDir.tempPath(), type=str))
        self.workDirName.textChanged.connect (lambda value : settings.setValue("SOSClient/workDir", value))
    
    @property
    def selectedOffering (self):
        try:
            return self.cmbOfferings.itemData(self.cmbOfferings.currentIndex())
        except: return ""
    
    @property
    def selectedProperties (self):
        try: return self.lstProperties.model().stringListChecked
        except: return []
        
    @property
    def selectedFeaturesOfInterest (self):
        try: return self.lstFeatures.model().stringListChecked
        except: return []
        
    @property
    def selectedProcedures (self):
        try: return self.lstProcedures.model().stringListChecked
        except: return []
            
    @property
    def selectedResultModel (self):
        try: return self.cmbResultModel.currentText()
        except: return ""
        
    @property
    def selectedWorkDir (self):
        try: return self.workDirName.text
        except: return ""
    
    def populateConnectionList(self):
        self.cmbConnections.blockSignals(True)
        self.cmbConnections.clear()
        keys = QgsOWSConnection.connectionList("SOS")
        self.cmbConnections.addItems (keys)
        self.cmbConnections.blockSignals(False)
        index = self.cmbConnections.findText(QgsOWSConnection.selectedConnection("SOS"))
        self.cmbConnections.setCurrentIndex(index)
        self.on_cmbConnections_currentIndexChanged (QgsOWSConnection.selectedConnection("SOS"))
        QgsDebug ("populateConnectionList: selectedConnection = {}".format(QgsOWSConnection.selectedConnection("SOS")))
        
    @QtCore.pyqtSlot(str)
    def on_cmbConnections_currentIndexChanged (self, text):
        text = str(text)
        if QgsOWSConnection.selectedConnection("SOS") != text:
            QgsOWSConnection.setSelectedConnection("SOS", text)
            
        if text != "":
            self.btnConnect.setEnabled(True)
            self.btnEdit.setEnabled(True)
            self.btnDelete.setEnabled(True)
        else:
            self.btnConnect.setEnabled(False)
            self.btnEdit.setEnabled(False)
            self.btnDelete.setEnabled(False)

    @QtCore.pyqtSlot()
    def on_btnConnect_clicked(self):
        self.cmbOfferings.clear()
        self.htmlView.setText ("")
        self.btnAdd.setEnabled(False)
        self.btnConnect.setEnabled(False)
        
        connection = QgsOWSConnection("SOS", QgsOWSConnection.selectedConnection("SOS"))
        url = str(connection.uri().param('url'))
        
        QgsMessageLog.logMessage(self.tr("Connecting to {url}").format(url=url), "SosClient", QgsMessageLog.INFO)
        
        if url != "" :
            self.executeRequest(SensorObservationService.capabilitiesUrl(url), self.capabilitiesRequest)

    @QtCore.pyqtSlot()
    def on_btnNew_clicked(self):
        nc = QgsNewHttpConnection (self, "/Qgis/connections-sos/")
        nc.setWindowTitle(self.tr("Create a new SOS connection"))
        if nc.exec_():
            self.populateConnectionList()
    
    @QtCore.pyqtSlot()
    def on_btnEdit_clicked(self):
        nc = QgsNewHttpConnection (self, "/Qgis/connections-sos/", self.cmbConnections.currentText())
        nc.setWindowTitle(self.tr("Modify SOS connection"))
        if nc.exec_():
            self.populateConnectionList()
    
    @QtCore.pyqtSlot()
    def on_btnDelete_clicked(self):
        msg = str (self.tr("Are you sure you want to remove the %s connection and all associated settings?")) % (self.cmbConnections.currentText())
        result = QtGui.QMessageBox.information(self, self.tr("Confirm Delete"), msg, QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
        if result == QtGui.QMessageBox.Ok :
            QgsOWSConnection.deleteConnection("SOS", self.cmbConnections.currentText())
            self.populateConnectionList()
            
    @QtCore.pyqtSlot()
    def on_btnSave_clicked (self):
        pass
    
    @QtCore.pyqtSlot(int)
    def on_cmbOfferings_activated(self, index):
        offer = self.cmbOfferings.itemData(index) if index > -1 else ""
        QgsDebug ("on_cmbOfferings_activated {}: {}".format(index, offer))
        if offer in self.service.observationOfferingList:
            propertiesList = QStringListCheckableModel(self.service[offer].observedPropertiesList)
            propertiesList.dataChanged.connect(self.updateLayerName)
            self.lstProperties.setModel(propertiesList)
            featuresList = QStringListCheckableModel(self.service[offer].featureOfInterestList)
            featuresList.dataChanged.connect(self.featuresSelectedChange)
            self.lstFeatures.setModel(featuresList)
            self.lstProcedures.setModel(QStringListCheckableModel(self.service[offer].proceduresList))
            self.cmbFilterScalarOperands.setModel(QtGui.QStringListModel(self.service[offer].observedPropertiesList))
            self.filterRequest.scalarOperand = self.service[offer].observedPropertiesList[0]
            self.srsName = self.service[offer].srsName
            self.cmbResultModel.setModel(QtGui.QStringListModel(self.service[offer].resultModel))
            
        self.updateLayerName ()
        
    def updateLayerName (self):
        if not len(self.layerName.text()) or self.layerName.text() == self.lastLayerName:
                self.lastLayerName = self.selectedOffering
                properties = ",".join(self.selectedProperties)
                if len(properties):
                    self.lastLayerName += ": " + properties
                self.layerName.setText(self.lastLayerName)
        else:
            self.lastLayerName = ""
            self.layerName.setText(self.lastLayerName)
            
    def featuresSelectedChange (self):
        if  len(self.selectedFeaturesOfInterest) > 0 and \
            not self.lblSpatialFilterWarning.isVisibleTo(self.lblSpatialFilterWarning.parent()) and \
            self.grpFilterSpatial.isChecked():
            self.messageBar.pushMessage(self.lblSpatialFilterWarning.text(),QgsMessageBar.WARNING,10)
        self.lblSpatialFilterWarning.setVisible (len(self.selectedFeaturesOfInterest) > 0)
    
    def executeRequest (self, url, callback, post = None):
        self.messageBar.clearWidgets()
        self.cmbOfferings.setEnabled (False)
        self.tabWidget.setEnabled (False)
        
        if post:
            self.reply = QgsNetworkAccessManager.instance().post(QNetworkRequest(url),post)
        else:
            self.reply = QgsNetworkAccessManager.instance().get(QNetworkRequest(url))
            
        progressMessageBar = self.messageBar.createMessage(self.tr("Please wait while downloading"))
        progressBar = QtGui.QProgressBar(self)
        progressBar.setMinimum(0)
        progressBar.setFormat(self.tr("%v bytes downloaded!"))
        progressBar.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        
        def updateProgress (read, total):
            try:
                progressBar.setMaximum (total)
                progressBar.setValue (read)
            except: pass
        updateProgress (0,0)
        self.reply.downloadProgress.connect (updateProgress)
        progressMessageBar.layout().addWidget(progressBar)
        
        btnAbort = QtGui.QPushButton(self.tr("Abort"))
        btnAbort.clicked.connect(self.reply.abort)
        progressMessageBar.layout().addWidget(btnAbort)
        
        fd, replyFilename = mkstemp(suffix=".xml", prefix = callback.__name__, dir = self.selectedWorkDir())
        os.close(fd)
        replyFile = open (replyFilename, "w")
        
        def replyReadyRead ():
            try: replyFile.write (self.reply.readAll())
            except: pass
        self.reply.readyRead.connect(replyReadyRead)
        
        def finishRequest ():
            replyFile.close()
            self.cmbOfferings.setEnabled (True)
            self.tabWidget.setEnabled(True)
            self.messageBar.clearWidgets()
            if self.reply.error() != QNetworkReply.NoError:
                self.messageBar.pushMessage(self.reply.errorString(), QgsMessageBar.CRITICAL)
            else:
                callback(replyFilename)
            self.reply.deleteLater()
        self.reply.finished.connect(finishRequest)
        
        self.messageBar.pushWidget(progressMessageBar, QgsMessageBar.INFO)
        
    def capabilitiesRequest (self, fileName):
        try:
            self.service = SensorObservationService (self.reply.url(), fileName)
            self.filterRequest = FilterRequest (self.service)
        except Exception as error:
            self.service = None
            widget = self.messageBar.createMessage(unicode(error))
            button = QtGui.QCommandLinkButton (widget)
            button.setText(self.tr("Show reply"))
            button.clicked.connect(XmlViewerDialog (self, QtCore.QFile(fileName), XmlHighlighter).exec_)
            widget.layout().addWidget(button)
            self.messageBar.pushWidget(widget, QgsMessageBar.CRITICAL)
            
        if self.service:
            self.messageBar.pushMessage(self.tr("Capabilities downloaded"),QgsMessageBar.INFO,3)
            self.htmlView.setText (unicode(self.service))
            for offer in self.service.observationOfferingList:
                    self.cmbOfferings.addItem("%s (%s)" % (self.service[offer].name,self.service[offer].id), self.service[offer].id)
                    
            index = self.cmbOfferings.currentIndex()
            if index > -1: self.cmbOfferings.activated.emit(index)
            
            if 'GetObservation' in self.service.operationsMetadata:
                self.btnAdd.setEnabled(True)
                
                self.grpFilterSpatial.setChecked (self.filterRequest.spatialFilter == True)
                self.grpFilterSpatial.setEnabled (self.filterRequest.spatialFilter != None)
                self.cmbFilterSpatialOperators.setModel(QtGui.QStringListModel(self.service.spatialOperators))
                self.cmbFilterSpatialOperands.setModel(QtGui.QStringListModel(self.service.spatialOperands))
                self.cmbFilterSpatialOperands.activated.emit(self.cmbFilterSpatialOperands.currentIndex())
                
                self.grpFilterTemporal.setChecked (self.filterRequest.temporalFilter == True)
                self.grpFilterTemporal.setEnabled (self.filterRequest.temporalFilter != None)
                self.cmbFilterTemporalOperators.setModel(QtGui.QStringListModel(self.service.temporalOperators))
                self.cmbFilterTemporalOperands.setModel(QtGui.QStringListModel(self.service.temporalOperands))
                self.cmbFilterTemporalOperands.activated.emit(self.cmbFilterTemporalOperands.currentIndex())
                
                self.grpFilterScalar.setChecked (self.filterRequest.temporalFilter == True)
                self.grpFilterScalar.setEnabled (self.filterRequest.temporalFilter != None)
                self.cmbFilterScalarOperators.setModel(QtGui.QStringListModel(self.service.scalarOperators))
                self.cmbFilterScalarOperators.activated.emit(self.cmbFilterScalarOperators.currentIndex())
    
    @QtCore.pyqtSlot()
    def on_actionShowXML_triggered(self):
        try: XmlViewerDialog (self, self.service.capabilitiesXml, XmlHighlighter).exec_()
        except: pass
        
    @QtCore.pyqtSlot()
    def on_actionSelectAllProperties_triggered(self):
        try: self.lstProperties.model().checkAll()
        except: pass
        
    @QtCore.pyqtSlot()
    def on_actionSelectNoneProperties_triggered(self):
        try: self.lstProperties.model().checkNone()
        except: pass
        
    @QtCore.pyqtSlot()
    def on_actionSelectInvertProperties_triggered(self):
        try: self.lstProperties.model().checkInvert()
        except: pass
    
    @QtCore.pyqtSlot()
    def on_actionSelectAllFeatures_triggered(self):
        try: self.lstFeatures.model().checkAll()
        except: pass
        
    @QtCore.pyqtSlot()
    def on_actionSelectNoneFeatures_triggered(self):
        try: self.lstFeatures.model().checkNone()
        except: pass
        
    @QtCore.pyqtSlot()
    def on_actionSelectInvertFeatures_triggered(self):
        try: self.lstFeatures.model().checkInvert()
        except: pass
        
    @QtCore.pyqtSlot()
    def on_actionSelectAllProcedures_triggered(self):
        try: self.lstProcedures.model().checkAll()
        except: pass
        
    @QtCore.pyqtSlot()
    def on_actionSelectNoneProcedures_triggered(self):
        try: self.lstProcedures.model().checkNone()
        except: pass
        
    @QtCore.pyqtSlot()
    def on_actionSelectInvertProcedures_triggered(self):
        try: self.lstProcedures.model().checkInvert()
        except: pass
    
    @QtCore.pyqtSlot(bool)
    def on_grpFilterSpatial_toggled (self, check):
        self.filterRequest.spatialFilter = check
        QgsDebug ("FilterRequest: " + str(self.filterRequest))
    
    @QtCore.pyqtSlot(int)
    def on_cmbFilterSpatialOperators_activated(self, index):
        self.filterRequest.spatialOperator = self.cmbFilterSpatialOperators.currentText() if index > -1 else ""
    
    @QtCore.pyqtSlot(int)
    def on_cmbFilterSpatialOperands_activated(self, index):
        self.filterRequest.spatialOperand = self.cmbFilterSpatialOperands.currentText() if index > -1 else ""
        
        opWidget = self.laySpatialFilter.takeAt(1)
        if (opWidget):
            self.laySpatialFilter.removeItem(opWidget)
            opWidget.widget().deleteLater()
        
        opWidget = QLineEditButton (icon = QtGui.QIcon(":/plugins/SOSClient/coordinate_capture.png"))
        #opẀidget.setValidator()
        opWidget.setPlaceholderText(self.filterRequest.spatialOperand)
        opWidget.buttonClicked.connect(self.mapSelectionTool) 
        self.laySpatialFilter.addWidget (opWidget)
        opWidget.editingFinished.connect(self.spatialValueChanged)
        #TODO
        #if self.filterRequest.spatialOperand == "gml:Envelope":
        #    opWidget.setText (QgsGeometry.fromRect(self.service[self.selectedOffering].boundedBy).exportToWkt())
        
    def mapSelectionTool(self):
        self.hide()
        QgsDebug ("mapSelectionTool " + self.filterRequest.spatialOperand)
        tool = QgsMapToolCaptureSpatialOperand(self.iface.mapCanvas(), self.filterRequest.spatialOperand, self.srsName, self.sender())
        tool.selectionFinished.connect(self.mapSelectionToolFinished)
        self.iface.mapCanvas().setMapTool(tool)
        
    def mapSelectionToolFinished (self, wkt):
        tool = self.sender()
        if wkt: tool.parent.setText (wkt)
        tool.parent.editingFinished.emit()
        tool.selectionFinished.disconnect(self.mapSelectionToolFinished)
        tool.deactivate()
        del tool
        self.show()
    
    @QtCore.pyqtSlot(bool)
    def on_grpFilterTemporal_toggled (self, check):
        self.filterRequest.temporalFilter = check
        QgsDebug ("FilterRequest: " + str(self.filterRequest))
        
    @QtCore.pyqtSlot(int)
    def on_cmbFilterTemporalOperators_activated(self, index):
        self.filterRequest.temporalOperator = self.cmbFilterTemporalOperators.currentText() if index > -1 else ""
        
    @QtCore.pyqtSlot(int)
    def on_cmbFilterTemporalOperands_activated(self, index):
        self.filterRequest.temporalOperand = self.cmbFilterTemporalOperands.currentText() if index > -1 else ""
        
        opWidget = self.layTemporalFilter.takeAt(1)
        if (opWidget):
            self.layTemporalFilter.removeItem(opWidget)
            opWidget.widget().deleteLater()
        
        if self.filterRequest.temporalOperand == "gml:TimePeriod":
            opWidget = TimePeriodWidget()
        else:
            opWidget = TimeWidget()
        self.filterRequest.temporalValue = opWidget.text()
        self.layTemporalFilter.addWidget (opWidget)
        opWidget.editingFinished.connect(self.temporalValueChanged)
    
    @QtCore.pyqtSlot(bool)
    def on_grpFilterScalar_toggled (self, check):
        self.filterRequest.scalarFilter = check
        QgsDebug ("FilterRequest: " + str(self.filterRequest))
        
    @QtCore.pyqtSlot(int)
    def on_cmbFilterScalarOperators_activated(self, index):
        self.filterRequest.scalarOperator = self.cmbFilterScalarOperators.currentText() if index > -1 else ""
        
        opWidget = self.layScalarFilter.takeAt(1)
        if (opWidget):
            self.layScalarFilter.removeItem(opWidget)
            opWidget.widget().deleteLater()
        
        opWidget = QtGui.QLineEdit()
        opWidget.setPlaceholderText(self.filterRequest.scalarOperator)
        self.layScalarFilter.addWidget (opWidget)
        opWidget.editingFinished.connect(self.scalarValueChanged)
        
    @QtCore.pyqtSlot(int)
    def on_cmbFilterScalarOperands_activated(self, index):
        self.filterRequest.scalarOperand = self.cmbFilterScalarOperands.currentText() if index > -1 else ""
        
    @QtCore.pyqtSlot()
    def spatialValueChanged (self):
        widget = self.sender()
        self.filterRequest.spatialValue = widget.text()
        widget.blockSignals(True)
        widget.setText (self.filterRequest.spatialValue)
        widget.blockSignals(False)
        
    @QtCore.pyqtSlot()
    def temporalValueChanged (self):
        widget = self.sender()
        self.filterRequest.temporalValue = widget.text()
        widget.blockSignals(True)
        widget.setText (str(self.filterRequest.temporalValue))
        widget.blockSignals(False)
        
    @QtCore.pyqtSlot()
    def scalarValueChanged (self):
        widget = self.sender()
        self.filterRequest.scalarValue = widget.text()
        widget.blockSignals(True)
        widget.setText (str(self.filterRequest.scalarValue))
        widget.blockSignals(False)
    
    @QtCore.pyqtSlot (bool)
    def on_chkTimeManager_toggled (self, checked):
        if checked:
            if self.addLayerToTimeManager.__name__ == '<lambda>':
                try:
                    from timemanager.timemanager import timemanager
                    from timemanager.timevectorlayer import TimeVectorLayer
                    from timemanager.layer_settings import LayerSettings
                    def addTimeVectorLayer (layer, iface=self.iface):
                        ls = LayerSettings ()
                        ls.layer = layer
                        ls.layerName = layer.name()
                        ls.layerId = layer.id()
                        ls.startTimeAttribute = 'time'
                        ls.endTimeAttribute = 'time'
                        timeLayerManager = timemanager(iface).getController().getTimeLayerManager()
                        timeLayerManager.registerTimeLayer(TimeVectorLayer(ls))
                    self.addLayerToTimeManager = addTimeVectorLayer
                except ImportError:
                    self.messageBar.pushMessage(self.tr("TimeManager plugin is not instaled"), QgsMessageBar.WARNING, 5)
                    self.chkTimeManager.setChecked(False)
        self.createTimeManagerLayer = checked
           
    @QtCore.pyqtSlot()
    def on_actionAdd_triggered(self):
        if self.service:
            self.executeRequest(self.service.getObservationsUrl,
                                self.observationsRequest,
                                self.service.getObservations(offering = self.selectedOffering,
                                                             properties = self.selectedProperties,
                                                             features = self.selectedFeaturesOfInterest,
                                                             procedures = self.selectedProcedures,
                                                             filters = self.filterRequest,
                                                             resultModel = self.selectedResultModel))
        
    @QtCore.pyqtSlot()
    def on_actionEditRequest_triggered(self):
        if self.service:
            dlg = TextEditDialog (self,
                                  self.service.getObservations(offering = self.selectedOffering,
                                                               properties = self.selectedProperties,
                                                               features = self.selectedFeaturesOfInterest,
                                                               procedures = self.selectedProcedures,
                                                               filters = self.filterRequest,
                                                               resultModel = self.selectedResultModel),
                                  XmlHighlighter)
            if dlg.exec_():
                self.executeRequest(self.service.getObservationsUrl, self.observationsRequest, dlg.text)
          
    def observationsRequest (self, fileName):
        try:
            layer = ObservationsLayer (self.layerName.text(), fileName, only1stGeo = self.rdoFirstObsGeo.isChecked())
            
            def layerFinished ():
                if progressBar:
                    self.iface.mainWindow().statusBar().removeWidget(progressBar)
                    progressBar.deleteLater()
                layer.moveToThread(QtGui.QApplication.instance().thread())
                if thread:
                    thread.deleteLater()
                if not layer.vectorLayer.isValid():
                    widget = self.messageBar.createMessage(layer.error)
                    button = QtGui.QCommandLinkButton (widget)
                    button.setText(self.tr("Show reply"))
                    button.clicked.connect(XmlViewerDialog (self, QtCore.QFile(fileName), XmlHighlighter).exec_)
                    widget.layout().addWidget(button)
                    self.messageBar.pushWidget(widget, QgsMessageBar.CRITICAL)
                else :
                    QgsMapLayerRegistry.instance().addMapLayer(layer.vectorLayer)
                    if self.createTimeManagerLayer:
                        self.addLayerToTimeManager (layer.vectorLayer)
            
            progressBar = QtGui.QProgressBar(self)
            self.iface.mainWindow().statusBar().insertWidget(0, progressBar)
            progressBar.setToolTip(layer.name)
            progressBar.setRange(0,0)
            progressBar.setVisible (True)
            
            
            thread = QtCore.QThread(self)
            layer.moveToThread(thread)
            thread.started.connect (layer.toVectorLayer)
            layer.finished.connect (layerFinished, QtCore.Qt.QueuedConnection)
            thread.start()
        except Exception as error:
            widget = self.messageBar.createMessage(unicode(error))
            button = QtGui.QCommandLinkButton (widget)
            button.setText(self.tr("Show reply"))
            button.clicked.connect(XmlViewerDialog (self, QtCore.QFile(fileName), XmlHighlighter).exec_)
            widget.layout().addWidget(button)
            self.messageBar.pushWidget(widget, QgsMessageBar.CRITICAL)
            if thread:
                thread.deleteLater()
