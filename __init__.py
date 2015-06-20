# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SOSClient
                                 A QGIS plugin
 OGC Sensor Observation Sensor Client
                             -------------------
        begin                : 2014-11-26
        copyright            : (C) 2014 by Rubén Mosquera Varela
        email                : ruben.mosquera.varela@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load SOSClient class from file SOSClient.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from sos_client import SOSClient
    return SOSClient(iface)
