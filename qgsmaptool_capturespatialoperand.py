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

from qgis.gui import QgsMapTool, QgsRubberBand, QgsVertexMarker
from qgis.core import QGis, QgsGeometry, QgsPoint, QgsCoordinateTransform, QgsCoordinateReferenceSystem
from PyQt4 import QtCore, QtGui

class QgsMapToolCaptureSpatialOperand (QgsMapTool):
    """
    QGIS map tool. Draw a point, line, polygon or bounding box
    and convert it to WKT format.
    """
    
    selectionFinished = QtCore.pyqtSignal(str)
    
    def __init__(self, canvas, gmlOperand = "gml:Envelope", srsName="", parent = None):
        QgsMapTool.__init__ (self, canvas)
        self.canvas = canvas
        self.parent = parent
        if gmlOperand == "gml:Point":
            self.minPoints = 1 
            self.maxPoints = 1
            self.isPolygon = False
        elif gmlOperand == "gml:Envelope":
            self.minPoints = 2
            self.maxPoints = 2
            self.isPolygon = True
        elif gmlOperand == "gml:Polygon":
            self.minPoints = 3
            self.maxPoints = 0
            self.isPolygon = True
        elif gmlOperand == "gml:LineString":
            self.minPoints = 2
            self.maxPoints = 0
            self.isPolygon = False
        else:
            pass
        
        self.srsName = srsName
        self.rect = QtCore.QRect() if self.isPolygon and self.maxPoints == 2 else None

        if self.isPolygon:
            self.rubberBand = QgsRubberBand(self.canvas, QGis.Polygon)
        else:
            self.rubberBand = QgsRubberBand(self.canvas, QGis.Line)
            
        self.rubberBand.setColor(QtGui.QColor (255, 0,0, 150))
        self.rubberBand.setWidth(1)
        
        self.cursor = QtGui.QCursor (QtCore.Qt.CrossCursor)
        
        self.vertexMarkers = []
        self.captureList = []
        self.crs = QgsCoordinateReferenceSystem()
        self.crs.createFromUserInput(self.srsName)
        self.yx = self.crs.axisInverted()

    def canvasPressEvent(self, event):
        pass
                
    def canvasMoveEvent(self, event):
        if isinstance (self.rect, QtCore.QRect):
            self.rect.setBottomRight(event.pos())
            
        self.moveVertex(self.toMapCoordinates(event.pos()))

    def canvasReleaseEvent(self, event):
        numPoints = self.addVertex(self.toMapCoordinates(event.pos()))
        
        if numPoints == 1 and isinstance (self.rect, QtCore.QRect):
            self.rect.setTopLeft(event.pos())
        
        if  (event.button() == QtCore.Qt.RightButton and numPoints >= self.minPoints) or \
            (numPoints == self.maxPoints):
            self.finishGeom (numPoints)
            
    def keyReleaseEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.selectionFinished.emit(None)
            
    def activate(self):
        QgsMapTool.activate(self)
        self.canvas.setCursor(self.cursor)
  
    def deactivate(self):
        QgsMapTool.deactivate(self)
        self.canvas.unsetCursor()
        self.clearMapCanvas()
  
    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return False

    def addVertex(self, pt):
        self.rubberBand.addPoint(pt)
        m = QgsVertexMarker(self.canvas)
        m.setCenter(pt)
        self.vertexMarkers.append(m)
        
        #if self.yx: pt = QgsPoint(pt.y(),pt.x())
        self.captureList.append (pt)
        
        return len(self.captureList)

    def moveVertex(self, pt):
        if self.rubberBand.numberOfVertices() > 1:
            if isinstance (self.rect, QtCore.QRect):
                transform = self.canvas.getCoordinateTransform()
                ll = transform.toMapCoordinates( self.rect.left(), self.rect.bottom() );
                ur = transform.toMapCoordinates( self.rect.right(), self.rect.top() );
                self.rubberBand.reset(QGis.Polygon)
                self.rubberBand.addPoint( ll, False )
                self.rubberBand.addPoint( QgsPoint( ur.x(), ll.y() ), False )
                self.rubberBand.addPoint( ur, False )
                self.rubberBand.addPoint( QgsPoint( ll.x(), ur.y() ), True )
            else:
                self.rubberBand.movePoint(pt)
            
    def finishGeom (self, numPoints):
        if self.maxPoints == 1:
            geom = QgsGeometry.fromPoint(self.captureList[0])
        elif self.isPolygon and numPoints == 2:
            geom = QgsGeometry.fromPolyline(self.captureList)
            #geom = QgsGeometry.fromRect(geom.boundingBox())
        elif self.isPolygon:
            geom = QgsGeometry.fromPolygon([self.captureList])
        else:
            geom = QgsGeometry.fromPolyline(self.captureList)

        geom.simplify(0.00001)
        geom.transform(QgsCoordinateTransform(
                                              self.canvas.mapSettings().destinationCrs(),
                                              self.crs))
        
        if self.yx:
            i = 0
            vertex = geom.vertexAt(i)
            while (vertex != QgsPoint(0,0)):
                x = vertex.x()
                y = vertex.y()
                geom.moveVertex(y, x, i)
                i+=1
                vertex = geom.vertexAt(i) 
        
        self.selectionFinished.emit(geom.exportToWkt())
        self.clearMapCanvas()

    def clearMapCanvas(self):
        """
        Clears the map canvas and in particular the rubberband.
        A warning is thrown when the markers are removed.
        """
        # Reset the capture list
        self.captureList = []

        # Create an empty rubber band
        if self.isPolygon:
            self.rubberBand.reset(QGis.Polygon)
        else:
            self.rubberBand.reset(QGis.Line)

        # Delete also all vertex markers
        for marker in self.vertexMarkers:
            self.canvas.scene().removeItem(marker)
            del marker
  
        self.canvas.refresh()