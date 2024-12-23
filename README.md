# gml2geojson is a a GML-to-GeoJSON proxy using Python. 

# becuase of enshittiofiaction of GitHub, we moved to University Twente Gitlab: https://gitlab.utwente.nl/kobben/TMT/

It a simple Python CGI application, to wrap ogr2ogr functionality to convert WFS GML output into GeoJSON, in a web service. 

The Python CGI application parses the original URL, and does some limited checking and filtering. 
The service then invokes the ogr2ogr.py module. This is a direct Python port of the original ogr2ogr 
C++ code shipped with GDAL/OGR (which can be downloaded from the code repository at http://github.com/sourcepole/ogrtools/). 

More information can be found in a brief paper here:
http://www.geopython.net/pub/Journal_of_GeoPython_2_2017.pdf
