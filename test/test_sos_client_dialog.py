# coding=utf-8
"""Dialog test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = 'reuvem@gmail.com'
__date__ = '2014-11-26'
__copyright__ = 'Copyright 2014, Rubén Mosquera Varela'

import unittest

from PyQt4.QtGui import QDialogButtonBox, QDialog

from sos_client_dialog import SOSClientDialog

from utilities import get_qgis_app
QGIS_APP = get_qgis_app()

import SOSClient as SOSClient #@UnusedImport

class SOSClientDialogTest(unittest.TestCase):
    """Test dialog works."""

    def setUp(self):
        """Runs before each test."""
        self.dialog = SOSClientDialog(None)
        self.dialog.cmbConnections.addItems (["GOOGLE"])

    def tearDown(self):
        """Runs after each test."""
        self.dialog = None

    def test_dialog_cancel(self):
        """Test we can click close."""
        button = self.dialog.btnBox.button(QDialogButtonBox.Close)
        button.click()
        result = self.dialog.result()
        self.assertEqual(result, QDialog.Rejected)
        
    def test_cmbConnections_activated(self):
        """Test connection activated."""
        cmb = self.dialog.cmbConnections
        cmb.currentIndexChanged['QString'].emit ("GOOGLE")
        self.assertEqual(cmb.currentText(), "GOOGLE")

if __name__ == "__main__":
    suite = unittest.makeSuite(SOSClientDialogTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

