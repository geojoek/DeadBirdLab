# Script to solve for dead bird problem in ECO697K Dead Bird lab / Intro GIS Lab 3
# Joe Kopera ECO697K Spring 2020 - UMass Amherst

# Script to solve for thousands of dead birds, locations provided in shapefiles in a folder, one shapefile per bird.

# Environment dependencies: Python 3.x python interpreter installed with ArcGIS Pro 2.x (contains arcpy) + ArcPro 2.x
# This script stores intermediate processing layers in RAM.  For 1000+ birds I recommend having at least 8 GB free.

# This particular script is designed to be run from Windows powershell using:
# C:\Progra~1\ArcGIS\Pro\bin\Python\scripts\propy.bat deadbird_Scenario_Four.py
# Script for data only within Massachusetts and provided by MassGIS
# This script also presumes one has filtered and/or queried their wetlands and roads data to only include wetlands and roads and has repaired geometry on all input layers
# Please see deadbird_dataprep.py for script that prepares data for this script.

import datetime
import arcpy
from arcpy import env

def timestamp(message): # This is meant to replace print() or arcpy.AddMessage() in the script when I want to add messages.  It timestamps the messages so I can monitor performance of different stages in script.
    now = datetime.datetime.now()
    print(now.strftime("%H:%M:%S") + " - " + message)

timestamp("Modules loaded. Starting geoprocessing")

# PARAMETERS!-----------------------------

# input file location parameters
shapefileFolder = r""
roads = r""
wetlands = r""

# output file location parameters
mergedShapefiles = r""
sprayOutFile = r""
outfile_deadbirdBuffer = r""
outfile_roadbuffer = r""
outfile_wetlandbuffer = r""

# parameters for buffering. Distance in meters.
deadbirdBufferDist = "2000"
roadBufferDist = "50"
wetlandBufferDist = "100"

# Environment parameters
arcpy.env.workspace = shapefileFolder # This isn't most elegant solution but it's only way to get arcpy.listFiles below to work correctly, and using OS module is too much of a PITA for this application.
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(26986) # Sets Spatial Reference to NAD83 / Massachusetts Mainland just to ensure calculations are in meters
env.overwriteOutput = True # just for this one script for testing purposes
env.XYResolution = "0.01 Meters"
arcpy.env.XYTolerance = "0.01 Meters"

# setting up write-out-to-memory variables for intermediate, temporary datalayers mainly to help with autocomplete while I code further on in script
# writing intermediate geoprocessing steps out to in_memory to save file i/o's See https://pro.arcgis.com/en/pro-app/help/analysis/geoprocessing/modelbuilder/the-in-memory-workspace.htm
birdLocationsTemp = r"memory\birdLocations"
deadbirdBuffer = r"memory\deadBirdBuffer"
roadsTemp = r"memory\roadsTemp"
wetlandsTemp = r"memory\wetlandsTemp"
roadBuffer = r"memory\roadBuffer"
wetlandsBuffer = r"memory\wetlandsBuffer"
eraseTemp = r"memory\eraseOutput"
dissolvedClipInput = r"memory\dissolvedClipInput"


# END PARAMETERS!----------------------------

# iterate through individual dead bird shapefiles and append them into feature class in memory. Presumes you aren't iterating through list of old shapefiles as to not get duplicate data
timestamp("Appending all bird location shapefiles in {} to memory:".format(shapefileFolder))
shapefileList = arcpy.ListFiles("*.shp") # arcpy.ListFiles will only list files in env.workspace which is VERY SILLY
arcpy.CreateFeatureclass_management("memory", "birdLocations", "POINT") # creates empty feature class in RAM to append bird shapefiles to

for sf in shapefileList:
    timestamp("Processing {}".format(sf))
    arcpy.Append_management(sf, r"memory\birdLocations", "NO_TEST") # TEST Assumes all input shapefiles have same dataset schema - saves processing time. Will throw error if not.

timestamp("Writing out all bird locations to {}.".format(mergedShapefiles))
arcpy.CopyFeatures_management(birdLocationsTemp, mergedShapefiles) # writes out that layer in memory into shapefile because we can have a little shapefile, as a treat

# Create buffers around each dead bird and dissolves them so it's all one feature
timestamp("Creating {} meter buffer around dead bird locations".format(deadbirdBufferDist))
arcpy.Buffer_analysis(birdLocationsTemp, deadbirdBuffer, deadbirdBufferDist, "FULL", "ROUND", "ALL")
arcpy.Delete_management(birdLocationsTemp) # clears birdLocationsTemp from memory since we're not going to use it anymore
timestamp("Writing out road buffers to shapefile... just in case")
arcpy.CopyFeatures_management(deadbirdBuffer, outfile_deadbirdBuffer)

# Query roads and wetlands which intersect deadBirdBuffer and buffer those
timestamp("Creating temporary roads layer")
arcpy.MakeFeatureLayer_management(roads, roadsTemp)

timestamp("Selecting all roads that intersect with dead bird buffer")
selectedRoads = arcpy.SelectLayerByLocation_management(roads, "INTERSECT", deadbirdBuffer)

timestamp("Buffering all selected roads with dissolving all output features")
arcpy.Buffer_analysis(selectedRoads, roadBuffer, roadBufferDist, "FULL", "ROUND", "ALL")
arcpy.Delete_management(roadsTemp)

timestamp("Writing out road buffers to shapefile... just in case")
arcpy.CopyFeatures_management(roadBuffer, outfile_roadbuffer)

timestamp("Repairing Geometry of roads buffers just in case")
arcpy.RepairGeometry_management(roadBuffer) # Note: This takes 7-8 minutes and will make it seem like Python is stalling

timestamp("Creating temporary wetlands layer")
arcpy.MakeFeatureLayer_management(wetlands, wetlandsTemp)

timestamp("Selecting all wetlands that intersect with dead bird buffer")
selectedWetlands = arcpy.SelectLayerByLocation_management(wetlands, "INTERSECT", deadbirdBuffer)

timestamp("Buffering all selected wetlands")
arcpy.Buffer_analysis(selectedWetlands, wetlandsBuffer, wetlandBufferDist, "FULL", "ROUND", "ALL")
arcpy.Delete_management(wetlandsTemp)

timestamp("Writing out wetlands buffers to shapefile... just in case")
arcpy.CopyFeatures_management(wetlandsBuffer, outfile_wetlandbuffer)

timestamp("Repairing Geometry of wetlands buffers just in case")
arcpy.RepairGeometry_management(wetlandsBuffer) # Note: This takes forever and will make it seem like Python is stalling

# use erase tool to subtract wetlands buffer from road buffer and write out to shapefile
timestamp("Subtracting wetlands buffer from roads buffer since one can't spray there and writing out to {}".format(sprayOutFile))
arcpy.Erase_analysis(roadBuffer, wetlandsBuffer, eraseTemp) # N

# free up memory by getting rid of layers we will no longer use
timestamp("Deleting clip and wetlands buffers temporary layers from memory")
tempDataTrashCan = [wetlandsBuffer, roadBuffer]
for x in tempDataTrashCan:
    arcpy.Delete_management(x)

# timestamp("Dissolving output of Erase tool run above")
# arcpy.Dissolve_management(eraseTemp, dissolvedClipInput)

# Clip the output of the erase command and write out to file as your final result
timestamp("Clipping the result of the above subtraction and writing out to {}.".format(sprayOutFile))
arcpy.Clip_analysis(dissolvedClipInput, deadbirdBuffer, sprayOutFile)
arcpy.Delete_management(dissolvedClipInput)

# calculate percentage of total spraying radius given roads and wetland constraints
# Since we dissolve features in each buffer above there will only be one feature in the shapefile, but setting this Search Cursor up in case multiple features.
timestamp("Iterating through {} and adding up total area of all buffers".format(sprayOutFile))

# Solution here modified from https://gis.stackexchange.com/questions/57448/calculate-area-within-python-script-in-arcmap

# Calculate total area in sprayOutFile, which is areas we're allowed to spray
geometryField = arcpy.Describe(sprayOutFile).shapeFieldName #Get name of geometry field
cursor = arcpy.SearchCursor(sprayOutFile)

sprayArea = 0.00 # setting up area as floating point / double container for loop below
for row in cursor:
    featureArea = row.getValue(geometryField).area #Read area value as double
    sprayArea = sprayArea + featureArea
del row, cursor #Clean up cursor objects

# Calculate total area of 2000m buffers around all the dead birds
geometryField = arcpy.Describe(deadbirdBuffer).shapeFieldName #Get name of geometry field
cursor = arcpy.SearchCursor(deadbirdBuffer)

deadbirdBufferArea = 0.00
for row in cursor:
    featureArea = row.getValue(geometryField).area #Read area value as double
    deadbirdBufferArea = deadbirdBufferArea + featureArea
del row, cursor #Clean up cursor objects

percentArea = sprayArea / deadbirdBufferArea * 100

timestamp("Area that's able to be sprayed is {} square meters.\n Area that should be sprayed is {} square meters.\nArea that's able to be sprayed is {} percent of area that should be sprayed".format(sprayArea, deadbirdBufferArea, percentArea))
