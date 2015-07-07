# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SOSClient
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

from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QFile
from PyQt4.QtGui import QMenu, QAction, QIcon, QMessageBox
from qgis.gui import QgsMessageBar
from ui import resources_rc #@UnusedImport
from sos_client_dialog import SOSClientDialog
from xmlviewer_dialog import XmlViewerDialog
from xmlhighlighter import XmlHighlighter
from sosplot_dialog import SOSPlotDialog
import os.path

class SOSClient:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            '{}.qm'.format(locale))
        
        if not os.path.exists(locale_path):
            locale = locale.split('_')[0]
            locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            '{}.qm'.format(locale))
        
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = SOSClientDialog(iface = self.iface)

        # Declare instance attributes
        self.actions = []
        self.menu = QMenu(self.tr(u'&SOS Client'))
        self.toolbar = self.iface.addToolBar(u'SOSClient')
        self.toolbar.setObjectName(u'SOSClient')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('SOSClient', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.menu.addAction (action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        self.add_action(
            ':/plugins/SOSClient/icon_add.png',
            text=self.tr(u'SOS Client'),
            callback=self.run,
            parent=self.iface.mainWindow())

        self.add_action(
            ':/plugins/SOSClient/icon_xml.png',
            text=self.tr(u'Show XML'),
            callback=self.showLayerXml,
            parent=self.iface.mainWindow(),
            add_to_toolbar=True)
        
        self.add_action(
            ':/plugins/SOSClient/icon_plot.png',
            text=self.tr(u'Plot'),
            callback=self.showPlotDialog,
            parent=self.iface.mainWindow(),
            add_to_toolbar=True)

        self.add_action(
            ':/plugins/SOSClient/icon.png',
            text=self.tr(u'About'),
            callback=self.about,
            parent=self.iface.mainWindow(),
            add_to_toolbar=False)
        
        self.menu.setIcon(QIcon(':/plugins/SOSClient/icon.png'))
        self.iface.webMenu().addMenu (self.menu)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removeToolBarIcon(action)
        self.iface.webMenu().removeAction(self.menu.menuAction())

    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass
        
    def showLayerXml (self):
        layer = self.iface.activeLayer()
        if layer == None:
            self.iface.messageBar().pushMessage (self.tr(u'SOS Client'),self.tr("You must select a layer"), QgsMessageBar.WARNING, 10)
            return
        
        xml = layer.customProperty("xml")
        if len (xml):
            dlg = XmlViewerDialog (self.iface.mainWindow(), QFile(xml), XmlHighlighter)
            dlg.show()
            dlg.exec_()
        else:
            self.iface.messageBar().pushMessage (self.tr(u'SOS Client'),self.tr("Layer have not a xml property"), QgsMessageBar.WARNING, 10)
            
    def showPlotDialog (self):
        #try:
            dlg = SOSPlotDialog (self.iface.activeLayer(), parent=self.iface.mainWindow())
            dlg.show()
            dlg.exec_()
        #except Exception as error:
        #    self.iface.messageBar().pushMessage (self.tr(u'SOS Client'),unicode(error), QgsMessageBar.CRITICAL, 10)
    
    def about(self):
        #TODO
        QMessageBox.information(self.iface.mainWindow(), self.tr(u"About SOS Client"), 
                                self.tr(u"SOS Client Plugin<br />This plugin request observations data from OGC SOS server to create a vector layer.<br />Also provides tools to plot observations data<br /><br />Author: Rubén Mosquera Varela<br />E-mail: <a href=\"mailto:ruben.mosquera.varela@gmail.com\">ruben.mosquera.varela@gmail.com</a>"))
