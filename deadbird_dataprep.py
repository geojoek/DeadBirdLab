# Script to repair geometry and clean input roads and wetlands datalayers for ECO 697K Lab3: Dead Bird Lab

# Environment dependencies: Python 3.x python interpreter installed with ArcGIS Pro 2.x (contains arcpy) + ArcPro 2.x
# This script stores intermediate processing layers in RAM.  For 1000+ birds

# This particular script is designed to be run from Windows powershell using:
# C:\Progra~1\ArcGIS\Pro\bin\Python\scripts\propy.bat deadbird_dataprep.py
# Script for data only within Massachusetts and provided by MassGIS
# This script also presumes one has filtered and/or queried their wetlands and roads data to only include wetlands and roads and has repaired geometry on all input layers

import datetime
import arcpy
from arcpy import env

def timestamp(message): # This is meant to replace print() or timestamp() in the script when I want to add messages.  It timestamps the messages so I can monitor performance of different stages in script.
    now = datetime.datetime.now()
    print(now.strftime("%H:%M:%S") + " - " + message)

timestamp("Modules loaded. Starting geoprocessing")

# PARAMETERS!-----------------------------

# input file location parameters
workspace = r""
roads = r""
wetlands = r""

# output file locaton parameters
newOutFolder = r"\cleanData"
fixedRoads = "fixedRoads.shp"
fixedWetlands = "fixedWetlands.shp"

# environment parameters
arcpy.env.workspace = workspace
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(26986) # Sets Spatial Reference to NAD83 / Massachusetts Mainland just to ensure calculations are in meters
env.overwriteOutput = True # just for this one script for testing purposes
env.XYResolution = "0.01 Meters"
arcpy.env.XYTolerance = "0.01 Meters"

# temp files in RAM
roadsTemp = r"memory\roadsTemp"
wetlandsTemp = r"memory\wetlandsTemp"
roadslayer = r"memory\roadsLayer"
wetlandslayer = r"memory\wetlandsLayer"

# END PARAMETERS!-----------------------------


def stripFields(fcName): # defining function that will strip fields
    FCfields = [f.name for f in arcpy.ListFields(fcName)] # Got this from https://gis.stackexchange.com/questions/236779/removing-multiple-fields-in-arcpy-with-remove-function
    DontDeleteFields = ["Shape", "FID", "OBJECTID", "OBJECTID_1"] # These are fields that exist in these layers. Though OBJECTID_1 doesn't exist in wetlands at first... I think it gets created by arcpy when I load it into \memory
    # including OBJECTID_1 is not an ideal solution since I don't know why that field gets added, but it works...
    fields2Delete = list(set(FCfields) - set(DontDeleteFields))
    arcpy.DeleteField_management(fcName, fields2Delete)

timestamp("Creating {}{}".format(workspace, newOutFolder))
arcpy.CreateFolder_management(workspace, newOutFolder)

# dealing with the roads layer
timestamp("Loading roads layer into memory")
arcpy.CopyFeatures_management(roads, roadsTemp)
timestamp("Stripping fields from roads layer")
stripFields(roadsTemp)
timestamp("Reparing roads geometry")
arcpy.MakeFeatureLayer_management(roadsTemp, roadslayer)
arcpy.RepairGeometry_management(roadslayer, "DELETE_NULL")
newRoadPath = newOutFolder + "\\" + fixedRoads
timestamp("Writing new roads layer to {}\\{}".format(newOutFolder, fixedRoads))
arcpy.CopyFeatures_management(roadslayer, newRoadPath)
arcpy.Delete_management(roadsTemp, roadslayer)

# dealing with that nasty, nasty wetlands layer
timestamp("Loading wetlands layer into memory")
arcpy.CopyFeatures_management(wetlands, wetlandsTemp)
timestamp("Stripping fields from wetlands layer")
stripFields(wetlandsTemp)
timestamp("Reparing wetlands geometry")
arcpy.MakeFeatureLayer_management(wetlandsTemp, wetlandslayer)
arcpy.RepairGeometry_management(wetlandslayer, "DELETE_NULL")
newwetlandsPath = newOutFolder + "\\" + fixedWetlands
timestamp("Writing new wetlands layer to {}\\{}".format(newOutFolder, fixedWetlands))
arcpy.CopyFeatures_management(wetlandslayer, newwetlandsPath)
arcpy.Delete_management(wetlandslayer, wetlandsTemp)

timestamp("Script complete!")
