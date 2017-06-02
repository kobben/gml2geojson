#!/Library/Frameworks/Python.framework/Versions/3.5/bin/python3.5
# -- use !/usr/bin/python for python 2.7
# -- use !/Library/Frameworks/Python.framework/Versions/3.4/bin/python3.4 for python 3.4
# -- use !/Library/Frameworks/Python.framework/Versions/3.5/bin/python3.5 for python 3.5
# -*- coding: UTF-8 -*-

import sys, os, subprocess, unicodedata

# import cgi module and enable debugging:
import cgi
import cgitb
cgitb.enable()

# import ogr modules:
try:
    from osgeo import ogr, gdal, osr
except:
    sys.exit('ERROR: cannot find GDAL/OGR modules')
try:
    import ogr2ogr
except:
    sys.exit('ERROR: cannot import ogr2ogr.py')

# some utils to compare strings caseless:
def normalize_caseless(text):
    return unicodedata.normalize("NFKD", text.casefold())
def caseless_equal(left, right):
    return normalize_caseless(left) == normalize_caseless(right)


# print (sys.version)
# print ("GDAL/OGR version: " + gdal.VersionInfo('VERSION_NUM'))

# convert using the Python implementation of ogr2ogr:
def do_ogr2ogrPy():
    inFile = "wfs:" + baseurl + extraParams
    outFile = "/vsistdout/"  # send output to stdout = document.write in server
    # outFile = "/Users/barendkobben/Sites/gml2geojson/data/test.json"

    # note: ogr2ogr.py __main__ is expecting sys.argv, where the first argument is the script name
    # so, the arguments in the commands array need to be offset by 1
    command = ["", "-f", "GeoJSON", outFile, inFile, layername]

    # execute:
    ogr2ogr.main(command)


# convert using the native executable of ogr2ogr:
def do_ogr2ogr():
    inFile = "wfs:" + baseurl + extraParams
    outFile = "/vsistdout/"  # send output to stdout = document.write in server
    # outFile = "/Users/barendkobben/Sites/gml2geojson/data/test.json"

    # setup for running in unix BSD on localhost:
    command = ["/Library/Frameworks/GDAL.framework/Versions/2.1/Programs/ogr2ogr", "-f", "GeoJSON", outFile, inFile,
               layername]
    # setup for running in Windows on kartoweb.itc.nl:
    # command = [ "c:/ms4w/tools/gdal-ogr/ogr2ogr.exe", "-f",  "GeoJSON",  outFile, inFile, layerName]

    # execute:
    subprocess.check_call(command)


# convert using the ogr WFS reader into OGR features, then out to GeoJSON:
def do_ogrWFS():
    # Set the driver (optional)
    wfs_drv = ogr.GetDriverByName('WFS')

    # Speeds up querying WFS capabilities for services with alot of layers
    gdal.SetConfigOption('OGR_WFS_LOAD_MULTIPLE_LAYER_DEFN', 'NO')
    # Set config for paging. Works on WFS 2.0 services and WFS 1.0 and 1.1 with some other services.
    gdal.SetConfigOption('OGR_WFS_PAGING_ALLOWED', 'YES')
    gdal.SetConfigOption('OGR_WFS_PAGE_SIZE', '10000')

    wfs_ds = wfs_drv.Open("wfs:" + baseurl + extraParams)
    if not wfs_ds:
        sys.exit('ERROR: can not open WFS datasource [%s]') % (baseurl)
    else:
        pass

    layer = wfs_ds.GetLayerByName(layername)
    srs = layer.GetSpatialRef()
    epsg = srs.GetAttrValue('authority', 1)  # first child [0] = 'EPSG', second [1] = epsg code
    # print ('Layer: %s, Features: %s, SRS: %s...' % (layer.GetName(), layer.GetFeatureCount(), srs.ExportToWkt()))

    # print json featurecollection header
    print('{ "type": "FeatureCollection", ')
    print('"crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:EPSG::%s" } }, ' % (epsg))
    print('"features": [ ')

    # iterate over features
    feat = layer.GetNextFeature()
    firstOne = True
    while feat is not None:
        if (not firstOne):
            print(',')  # before features (except first one)
        firstOne = False
        geom = feat.GetGeometryRef()
        # geojson = geom.GetGeometryName()
        geojson = feat.ExportToJson()
        # geojson = geom.ExportToGML()
        # geojson = geom.ExportToJson()
        print(geojson)
        feat = layer.GetNextFeature()

    # print featurecollection footer
    print(' ] } ')

    # free memory
    feat = None
    layer = None
    wfs_drv = None
    wfs_ds = None



baseurl = ''
mapfile = ''
layername = ''
extraParams = ''
errorMsg = ''

theRequest = cgi.FieldStorage()
for KV in theRequest:
    if caseless_equal(KV, 'URL') :
        url = str(theRequest[KV].value).split('?')
        baseurl = url[0] + '?'
        firstKV = url[1]
        if firstKV != '':
            firstK = firstKV.split('=')[0]
            firstV = firstKV.split('=')[1]
            if caseless_equal(firstK, 'MAP') :
                mapfile = str(firstV)
            elif caseless_equal(firstK, 'TYPENAME') or caseless_equal(firstK, 'TYPENAMES') :
                layername = str(firstV)
            else :
                extraParams = extraParams + "&" + str(firstK) + "=" + str(firstV)
    elif caseless_equal(KV, 'MAP') :
        mapfile = str(theRequest[KV].value)
    elif caseless_equal(KV, 'TYPENAME') or caseless_equal(KV, 'TYPENAMES') : #accept 2.0.0 TYPENAMES, although will fail with > 1:
        layername = str(theRequest[KV].value)
    elif caseless_equal(KV, 'SERVICE') :
        # should be absent or 'WFS'
        if not caseless_equal(theRequest[KV].value, 'WFS') :
            errorMsg = errorMsg + "<br>Parameter SERVICE should be 'WFS'"
    elif caseless_equal(KV, 'REQUEST') :
        # should be absent or 'GetFeature'
        if not caseless_equal(theRequest[KV].value, 'GetFeature') :
            errorMsg = errorMsg + "<br>Parameter REQUEST should be 'GetFeature'"
    elif caseless_equal(KV, 'RESULTTYPE') :
        # should be absent or 'results'
        if not caseless_equal(theRequest[KV].value, 'results') :
            errorMsg = errorMsg + "<br>Parameter RESULTTYPE should be 'results'"
    else:
        # all other parameters are just forwarded "as is"
        extraParams = extraParams + "&" + str(KV) + "=" + str(theRequest[KV].value)

#make sure Mapserver URLs include the mapfile parameter
if mapfile != '':
    baseurl = baseurl + 'map=' + mapfile + '&'

if baseurl == '?' or baseurl == '':
    errorMsg = errorMsg + "<br>Cannot determine base url."

if layername == '' :
    errorMsg = errorMsg + "<br>Cannot determine layername, probably TYPENAME parameter is missing"

if errorMsg != '' :
    print('Content-type: text/html')
    print('')
    print ('<HTML><HEAD><TITLE>ERROR</TITLE></HEAD>')
    print ('<BODY>')
    print ('<h2>ERROR in gml2geojson proxy</h2>')
    # note the empty print line above is required!
    print('baseurl = ' + baseurl)
    print('<br/>')
    print('layername = ' + layername)
    print('<br/>')
    print('extraParams = ' + extraParams)
    print('<p><b>Error(s) encountered:</b>')
    print(errorMsg)
    print ('</BODY></HTML>')
else :
    print('Content-type: application/json;charset=utf-8')
    print('')
    # note the empty print line above is required!
    do_ogr2ogrPy()
    # do_ogr2ogr()
    # do_ogrWFS()
