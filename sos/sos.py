# -*- coding: utf-8 -*-
"""
 sos module
"""

from sosparser import * #@UnusedWildImport
from qgstime import QgsTimeInstant, QgsTimePeriod
from PyQt4.QtCore import QUrl, QObject, QFile, pyqtSlot, pyqtSignal, Qt, QVariant
from PyQt4.QtXml import QDomDocument
from qgis.core import QgsGeometry, QgsRectangle, QgsOgcUtils, QgsFields, QgsField, QgsFeature, QgsCoordinateReferenceSystem, QGis, QgsVectorFileWriter, QgsVectorLayer

class SensorObservationService (QObject):
    """
    Represent a Sensor Observation Service
    """
    def __init__(self, url, xmlFile=None):
        """
        :param url: Sensor Observation Service URL
        :type str
        :param xmlFile: XML capabilities filename
        :type str
        """
        super (SensorObservationService, self).__init__()
        
        self._url = url
        self._capabilities = SOSCapabilities ()
        
        if xmlFile:
            xml = QFile (xmlFile)
            self._capabilities = XMLParserFactory.getInstance("SOSCapabilities")().parse(xml)

    @staticmethod
    def capabilitiesUrl(url):
        _url = QUrl (url)
        _url.addQueryItem("Service", "SOS")
        _url.addQueryItem("AcceptVersions", "1.0.0")
        _url.addQueryItem("Request","GetCapabilities")
        return _url
    
    @property
    def version(self):
        return '1.0.0'

    @property
    def url (self):
        return self._url

    @property
    def capabilitiesVersion (self):
        try:
            return self._capabilities.version
        except AttributeError:
            return ""

    @property
    def capabilitiesXml (self):
        try:
            return self._capabilities.xml
        except AttributeError:
            return ""
        
    @property
    def identification (self):
        try:
            return self._capabilities.serviceIdentification
        except AttributeError:
            return SOSServiceIdentification()

    @property
    def provider (self):
        try:
            return self._capabilities.serviceProvider
        except AttributeError:
            return SOSServiceProvider()

    @property
    def observationOfferingList (self):
        try:
            return self._capabilities.observationOfferingList.keys()
        except AttributeError:
            return []
    
    @property
    def operationsMetadata (self):
        try:
            return self._capabilities.operationsMetadata
        except AttributeError:
            return {}
    
    @property
    def getObservationsUrl (self):
        try:
            url = QUrl(self.operationsMetadata['GetObservation'].methods['Post'])
            #Para servidores mal configurados
            if url.host() == 'localhost':
                url.setHost (self.url.host())
                url.setPort (self.url.port())
                return url
            return url
        except:
            return QUrl()
        
    @property
    def spatialOperands (self):
        try:
            return self._capabilities.filterCapabilities.spatial_operands
        except AttributeError:
            return []
    
    @property
    def spatialOperators (self):
        try:
            return self._capabilities.filterCapabilities.spatial_operators
        except AttributeError:
            return []

    @property
    def temporalOperands (self):
        try:
            return self._capabilities.filterCapabilities.temporal_operands
        except AttributeError:
            return []
    
    @property
    def temporalOperators (self):
        try:
            return self._capabilities.filterCapabilities.temporal_operators
        except AttributeError:
            return []
    
    @property
    def scalarOperators (self):
        try:
            return self._capabilities.filterCapabilities.scalar_operators
        except AttributeError:
            return []

    def __getitem__(self, offer):
        if offer in self._capabilities.observationOfferingList.keys():
            return self._capabilities.observationOfferingList[offer]
        else:
            raise KeyError ("No Observational Offering with id: %s" % offer)
    
    def __unicode__ (self):
        return "<html><body>"+"".join(
                         map (lambda title, text:
                              '<p class="subheaderglossy">' + title + '</p><p>' + text + '</p>', [
                                self.tr ('Identification'),
                                self.tr ('Provider')
                                ],[
                                unicode (self.identification),
                                unicode (self.provider)])) + "</body></html>"
        
    def getObservations (self, offering="", properties=[], features=[], procedures=[], filters=None, resultModel = ""):
        """
        :param offering: Offering name
        :type offering: str
        :param properties: Selected properties names
        :type properties: str list
        :param features: Selected features of interest names
        :type features: str list
        :param procedures: Selected procedures names
        :type procedures: str list
        :param filters: Configured filters
        :type filters: FilterRequest
        :param resultModel: Selected result model
        :type resultModel: str
        :return: xml data
        """
        doc = QDomDocument()
        
        doc.appendChild(doc.createProcessingInstruction('xml', 'version="1.0" encoding="UTF-8"'))
        root = doc.createElement('GetObservation')
        root.setAttribute('xmlns',"http://www.opengis.net/sos/1.0")
        root.setAttribute('xmlns:ows',"http://www.opengis.net/ows/1.1")
        root.setAttribute('xmlns:gml',"http://www.opengis.net/gml")
        root.setAttribute('xmlns:ogc',"http://www.opengis.net/ogc")
        root.setAttribute('xmlns:om',"http://www.opengis.net/om/1.0")
        root.setAttribute('xmlns:xsi',"http://www.w3.org/2001/XMLSchema-instance")
        root.setAttribute('xsi:schemaLocation',"http://www.opengis.net/sos/1.0 http://schemas.opengis.net/sos/1.0.0/sosGetObservation.xsd")
        root.setAttribute('service',"SOS")
        root.setAttribute('version',"1.0.0")
        root.setAttribute('srsName',self[offering].srsName)
        doc.appendChild(root)
        
        offer = doc.createElement("offering")
        offer.appendChild(doc.createTextNode(offering))
        root.appendChild (offer)
        
        if filters.temporalFilter:
            timeEvent = doc.createElement("eventTime")
            operator = doc.createElement("ogc:%s" % filters.temporalOperator)
            prop = doc.createElement("ogc:PropertyName")
            prop.appendChild (doc.createTextNode ("om:samplingTime"))
            operand = doc.createElement(filters.temporalOperand)
            if filters.temporalOperand == "gml:TimeInstant":
                timePos = doc.createElement("gml:timePosition")
                timePos.appendChild(doc.createTextNode(str(filters.temporalValue)))
                operand.appendChild (timePos)
            elif filters.temporalOperand == "gml:TimePeriod":
                begin = doc.createElement("gml:beginPosition")
                begin.appendChild(doc.createTextNode(str(filters.temporalValue).split()[0]))
                end = doc.createElement("gml:endPosition")
                end.appendChild(doc.createTextNode(str(filters.temporalValue).split()[-1]))
                operand.appendChild(begin)
                operand.appendChild(end)
            
            root.appendChild(timeEvent)
            timeEvent.appendChild(operator)
            operator.appendChild (prop)
            operator.appendChild (operand)
        
        for proc in procedures:
            procElement = doc.createElement("procedure")
            procElement.appendChild (doc.createTextNode(proc))
            root.appendChild (procElement)
            
        for prop in properties:
            propElement = doc.createElement("observedProperty")
            propElement.appendChild(doc.createTextNode(prop))
            root.appendChild (propElement)
            
        foi = doc.createElement("featureOfInterest") if len (features) else None
        for foiName in features:
            foiElement = doc.createElement("ObjectID")
            foiElement.appendChild(doc.createTextNode(foiName))
            foi.appendChild (foiElement)
        
        if filters.spatialFilter and not foi:
            foi = doc.createElement("featureOfInterest")
            operator = doc.createElement("ogc:%s" % filters.spatialOperator)
            prop = doc.createElement("ogc:PropertyName")
            prop.appendChild (doc.createTextNode ("urn:ogc:data:location"))
            operator.appendChild (prop)
            
            try:
                if filters.spatialOperand == "gml:Point":
                    gmlNode = QgsOgcUtils.geometryToGML(QgsGeometry.fromPoint(filters._spatialValue), doc)
                elif filters.spatialOperand == "gml:Envelope":
                    gmlNode = QgsOgcUtils.rectangleToGMLEnvelope(QgsGeometry.fromRect(filters._spatialValue).boundingBox(), doc)
                elif filters.spatialOperand == "gml:Polygon":
                    gmlNode = QgsOgcUtils.geometryToGML(QgsGeometry.fromPolygon(filters._spatialValue), doc)
                elif filters.spatialOperand == "gml:LineString":
                    gmlNode = QgsOgcUtils.geometryToGML(QgsGeometry.fromPolyline(filters._spatialValue), doc)
                gmlNode.setAttribute('srsName',self[offering].srsName)
                operator.appendChild (gmlNode)
            except:
                pass
            foi.appendChild(operator)
            
        #Lista de features o filtro espacial
        if foi:
            root.appendChild(foi)
            
        if filters.scalarFilter:
            result = doc.createElement("result")
            operator = doc.createElement("ogc:PropertyIs%s" % filters.scalarOperator)
            prop = doc.createElement("ogc:PropertyName")
            prop.appendChild (doc.createTextNode (filters.scalarOperand))
            operator.appendChild (prop)
            
            if filters.scalarOperator in ["Between"]:
                try:
                    lower = doc.createElement ("ogc:LowerBoundary")
                    lowValue = doc.createElement ("ogc:Literal")
                    lowValue.appendChild(doc.createTextNode(str(filters.scalarValue).split()[0]))
                    lower.appendChild (lowValue)
                    upper = doc.createElement ("ogc:UpperBoundary")
                    upValue = doc.createElement ("ogc:Literal")
                    upValue.appendChild(doc.createTextNode(str(filters.scalarValue).split()[-1]))
                    upper.appendChild (upValue)
                    operator.appendChild (lower)
                    operator.appendChild (upper)
                except:
                    pass
            else:
                value = doc.createElement ("ogc:Literal")
                value.appendChild(doc.createTextNode(str(filters.scalarValue)))
                operator.appendChild (value)
                
            root.appendChild(result)
            result.appendChild(operator)
        
        responseFormat = doc.createElement ("responseFormat")
        responseFormat.appendChild (doc.createTextNode('text/xml;subtype="om/1.0.0"'))
        root.appendChild (responseFormat)
        
        resultModelElement = doc.createElement ("resultModel")
        resultModelElement.appendChild (doc.createTextNode(resultModel))
        root.appendChild (resultModelElement)
        
        responseMode = doc.createElement ("responseMode")
        responseMode.appendChild (doc.createTextNode("inline"))
        root.appendChild (responseMode)
        
        return doc.toString(4)
        
class SOSCapabilities ():
    """
    Capabilities data
    """
    def __init__(self):
        self.xml = ""
        self.version = ""
        self.serviceIdentification = None
        self.serviceProvider = None
        self.operationsMetadata = {}
        self.filterCapabilities = None
        self.observationOfferingList = {}

class SOSServiceIdentification (QObject):
    """
    Service Identification data
    """
    def __init__(self) :
        super (SOSServiceIdentification, self).__init__()
        self.title = ""
        self.abstract = ""
        self.keywords = []
        self.serviceType = ""
        self.serviceTypeVersion = ""

    def __unicode__ (self):
        return "".join(
                         map (lambda title, text:
                              '<p class="glossy">' + title + '</p><p>' + text + '</p>', [
                                self.tr ('Title'),
                                self.tr ('Abstract'),
                                self.tr ('Keywords'),
                                self.tr ('Service')
                                ],[
                                self.title,
                                self.abstract,
                                ", ".join(self.keywords),
                                self.serviceType +' (' + self.serviceTypeVersion +')']))

class SOSServiceProvider (QObject):
    """
    Service Provider data
    """
    def __init__(self) :
        super (SOSServiceProvider, self).__init__()
        self.providerName = ""
        self.providerSite = ""
        self.phones = {}
        self.address = {}
    
    def __unicode__ (self):
        return "".join(
                         map (lambda title, text:
                              '<p class="glossy">' + title + '</p><p>' + text + '</p>', [
                                self.tr ('Name'),
                                self.tr ('Site'),
                                self.tr ('Phones'),
                                self.tr ('Address')
                                ],[
                                self.providerName,
                                self.providerSite,
                                " ".join(self.phones.values()),
                                "<br>".join(self.address.values())]))

class SOSOperationMetadata ():
    """
    Operations metadata
    """
    def __init__(self):
        self.name = ""
        self.methods = {}
        self.parameters = {}

class SOSFilterCapabilities ():
    """
    Filter capabilities data
    """
    def __init__(self):
        self.spatial_operands = []
        self.spatial_operators = []
        self.temporal_operands = []
        self.temporal_operators = []
        self.scalar_operators = []

class SOSObservationOffering ():
    """
    Observation offering data
    """
    def __init__(self) :
        self.id = ""
        self.name = ""
        self.description = ""
        self.srsName = ""
        self.boundedBy = None
        self.time = None
        self.proceduresList = []
        self.observedPropertiesList = []
        self.featureOfInterestList = []
        self.responseFormat = ""
        self.resultModel = []
        self.responseMode = ""
        
class FilterRequest (object):
    """
    Filter request: Spatial, Temporal and Scalar with Operator and Operands
    """
    def __init__(self, service):
        assert isinstance(service, SensorObservationService)        
        self._service = service
        
        self.spatialFilter = None
        if len(self._service.spatialOperators) > 0:
            self.spatialFilter = False
            self.spatialOperator = self._service.spatialOperators[0]
            self.spatialOperand  = self._service.spatialOperands [0]
            self._spatialValue    = None
            
        self.temporalFilter = None
        if len(self._service.temporalOperators) > 0:
            self.temporalFilter = False
            self.temporalOperator = self._service.temporalOperators[0]
            self.temporalOperand  = self._service.temporalOperands [0]
            self._temporalValue   = None
            
        self.scalarFilter = None
        if len(self._service.scalarOperators):
            self.scalarFilter = False
            self.scalarOperator = self._service.scalarOperators[0]
            self.scalarOperand  = ""
            self._scalarValue    = None
    
    @property
    def spatialValue (self):
        try:
            if self._spatialValue == None:
                raise ValueError
            if self.spatialOperand == "gml:Point":
                return QgsGeometry.fromPoint(self._spatialValue).exportToWkt()
            elif self.spatialOperand == "gml:Envelope":
                return QgsGeometry.fromRect(self._spatialValue).exportToWkt()
            elif self.spatialOperand == "gml:Polygon":
                return QgsGeometry.fromPolygon(self._spatialValue).exportToWkt()
            elif self.spatialOperand == "gml:LineString":
                return QgsGeometry.fromPolyline(self._spatialValue).exportToWkt()
            else:
                raise ValueError
        except:
            return ""
    
    @spatialValue.setter        
    def spatialValue (self, value):
        try:
            if value.__len__:
                geom = QgsGeometry.fromWkt(value)
            else:
                raise ValueError
            if self.spatialOperand == "gml:Point":
                self._spatialValue = geom.asPoint()
            elif self.spatialOperand == "gml:Envelope":
                self._spatialValue = geom.boundingBox()
            elif self.spatialOperand == "gml:Polygon":
                self._spatialValue = geom.asPolygon()
            elif self.spatialOperand == "gml:LineString":
                self._spatialValue = geom.asPolyline()
            else:
                raise ValueError
        except:
            self._spatialValue = None
    @property
    def temporalValue (self):
        try:
            return self._temporalValue if self._temporalValue else ""
        except:
            return ""
        
    @temporalValue.setter        
    def temporalValue (self, value):
        if self.temporalOperand == "gml:TimeInstant":
            self._temporalValue = QgsTimeInstant (value)
        elif self.temporalOperand == "gml:TimePeriod":
            self._temporalValue = QgsTimePeriod (value.split()[0], value.split()[-1])
        else:
            self._temporalValue = value
        
    @property
    def scalarValue (self):
        try:
            return self._scalarValue if self._scalarValue else ""
        except:
            return ""
        
    @scalarValue.setter        
    def scalarValue (self, value):
        self._scalarValue = value

    def __str__(self):
        return "Spatial: {} {} {} {}; Temporal: {} {} {} {}; Scalar: {} {} {} {}".format(self.spatialFilter,self.spatialOperator, self.spatialOperand, self.spatialValue, self.temporalFilter, self.temporalOperator, self.temporalOperand, self.temporalValue, self.scalarFilter, self.scalarOperator, self.scalarOperand, self.scalarValue)

        
class ExceptionReport(Exception):
    """
    SOS Exception
    """
    def __init__(self, exceptionCode, exceptionText):
        self.__exceptionCode = exceptionCode
        self.__exceptionText = exceptionText

    @property
    def exceptionCode(self):
        return self.__exceptionCode if self.__exceptionCode else ""

    @property
    def exceptionText(self):
        return self.__exceptionText if self.__exceptionText else ""

    def __str__(self):
        return self.exceptionCode + ": " + self.exceptionText
    
class SOSProvider (object):
    """
    Fake QgsVectorDataProvider
    """
    def __init__(self):
        self.srsName = ""
        self.extent = QgsRectangle () 
        self.features = {}
        self.fields = [QgsField("foi", QVariant.String), QgsField("name", QVariant.String)]
        self._observations = {}
        self.only1stGeo = False
        
    def setObservation (self, foi, time, observedProperty, value):
        """
        :param foi: Feature Of Interest
        :type foi: str
        :param time: Phenomenom Time
        :type time: str
        :param observedProperty: Property
        :type observedProperty: str
        :param value: observed value
        :type value: float
        """
        try:
            timeList, propertiesList = self._observations[foi]
            propertiesList[timeList.index(time)][observedProperty] = value    
        except ValueError:
            #Ya existe registro para la foi, pero no para time
            timeList.append(time)
            propertiesList.append({observedProperty: value})
        except KeyError:
            #No existe registro para la foi
            timeList = []
            propertiesList = []
            self._observations[foi] = (timeList,propertiesList)
            timeList.append(time)
            propertiesList.append({observedProperty: value})
            
    def getObservation (self, foi="", time = None):
        """
        Only for testing purposes!
        """
        text = ""
        for foi in self._observations.keys():
            text += ";" + foi + ": " 
            timeList, propertiesList = self._observations[foi]
            for i in range(len(timeList)):
                text += str(timeList[i].toString(Qt.ISODate)) + "-" + str(propertiesList[i]) + ","
        return text
    
    def getFeatures (self):
        """
        :return QgsFeaures generator
        """
        fields = QgsFields()
        map (fields.append, self.fields)
        foiIds = {foiId : [] for foiId in self.features}
        try:
            idIsTuple = isinstance (eval(self._observations.keys()[0]),tuple)
        except:
            idIsTuple = False
        if idIsTuple:
            map (lambda x: foiIds[eval(x)[0]].append(x), self._observations.keys())
        else:
            map (lambda x: foiIds[x].append(x), self.features)
        for foi in self.features:
            name, geo = self.features[foi]
            for foi_id in foiIds[foi]:
                timeList, propertiesList = self._observations[foi_id]
                #for i,t in enumerate(timeList):
                for i, t in sorted({i:t for i,t in enumerate(timeList)}.items(), key=lambda x:x[1]):
                    values = []
                    for f in self.fields[3:]: #TODO si no tiene time esto no va a funcionar...
                        try:
                            values.append(propertiesList[i][str(f.name())])
                        except KeyError:
                            values.append (f.name())
                    
                    feature = QgsFeature (fields)
                    if geo:
                        feature.setGeometry (geo)
                        if self.only1stGeo: geo = None
                    feature.setAttributes([foi, name, t.toString(Qt.ISODate)] + values)
                    yield feature
                
class ObservationsLayer (QObject):
    """
    Encapsulate QgsVectorLayer generation
    """
    finished = pyqtSignal ()
    failed = pyqtSignal (unicode)
    
    def __init__(self, name = "Observations", xmlFile=None, only1stGeo = False):
        """
        :param name Layer name
        :type str
        :param xmlFile XML Observations filename
        :type str
        :param only1stGeo If True only first occurrence by foi will include geometric data 
        :type bool
        """
        super (ObservationsLayer, self).__init__()
        self._name = name
        self.features = []
        self.provider = None
        self.xmlFile = xmlFile
        self._layer = None
        self._error = None
        self._only1stGeo = only1stGeo
        
    @property
    def name (self):
        return self._name
    
    @pyqtSlot ()    
    def toVectorLayer (self):
        """
        Generate QgsVectorLayer
        """
        try:
            if self.xmlFile:
                xml = QFile (self.xmlFile)
                self.provider = XMLParserFactory.getInstance("SOSObservations")().parse(xml)
                self.provider.only1stGeo = self._only1stGeo
            
            layer = self._toVectorLayer_geojson()
            layer.setCustomProperty("xml", self.xmlFile)
            self._layer = layer
            self._error = None
        except Exception as error: 
            self._layer = None
            self._error = unicode(error)
        finally:
            self.finished.emit()
    
    @property
    def vectorLayer (self):
        if self._layer:
            return self._layer
        else:
            return QgsVectorLayer()
    
    @property    
    def error (self):
        if not self._error and not self.vectorLayer.isValid():
            self._error = self.tr("Invalid layer")
        return self._error if self._error else ""
    
#     def toVectorLayer_sqlite (self):        
#         crs = QgsCoordinateReferenceSystem()
#         crs.createFromUserInput(self.provider.srsName)
#         
#         fileName = self.xmlFile.replace(".xml", ".sqlite")
#         fields = QgsFields ()
#         map (fields.append, self.provider.fields)
#         writer = QgsVectorFileWriter (fileName, "utf-8", fields, QGis.WKBPoint, crs, "SQLite")
# 
#         if writer.hasError() != QgsVectorFileWriter.NoError:
#             raise Exception (writer.errorMessage())
#         
#         for feature in self.provider.getFeatures():
#             
#             self.features.append(feature)
#             writer.addFeature(feature)
#         
#         del writer #Forzar escritura a disco
#         
#         return QgsVectorLayer( fileName, self.name, "ogr")

    def _toVectorLayer_geojson (self):        
        crs = QgsCoordinateReferenceSystem()
        crs.createFromUserInput(self.provider.srsName)
        
        fileName = self.xmlFile.replace(".xml", ".geojson")
        fields = QgsFields ()
        map (fields.append, self.provider.fields)
        writer = QgsVectorFileWriter (fileName, "utf-8", fields, QGis.WKBPoint, crs, "GeoJSON")

        if writer.hasError() != QgsVectorFileWriter.NoError:
            raise Exception (writer.errorMessage())
        
        for feature in self.provider.getFeatures():
            self.features.append(feature)
            writer.addFeature(feature)
        
        del writer #Forzar escritura a disco
        
        return QgsVectorLayer( fileName, self.name, "ogr")
    
#     def toVectorLayer_memory (self):
#         def qgsSrsName (srsName = ""):
#             import re
#             m = re.match (".*(EPSG:[0-9]+)$",srsName)
#             return m.groups()[-1] if m else ""
#         
#         path = ("Point?type=SOS&crs={srs!s}&field=").format(srs=qgsSrsName(self.provider.srsName))
#         path += "&field=".join (map (lambda f: (str(f.name()) + ":") + ("double" if f.type() == QVariant.Double else "string"), self.provider.fields))
#         path += "&index=yes"
#         
#         for feature in self.provider.getFeatures():
#             self.features.append(feature)
#         
#         layer = QgsVectorLayer (path, self._name, "memory")
#         layerProvider = layer.dataProvider()
#         layer.startEditing()
#         layerProvider.addFeatures (self.features)
#         layer.commitChanges()
#         
#         return layer

    def __str__(self):
        return self.provider.getObservation()
