# DeadBirdLab
## ArcPy and other Python scripts to solve hypothetical public health GIS problem. ##

These are geoprocessing scripts in ArcPy and Python 3.x to solve a hypothetical problem posed in the Spring 2020 GIS Programming Course (ECO 697K) taught by my colleague Dr. Forrest Bowlick at U-Mass Amherst. Affectionately known as the "Revenge of Dead Birds! Lab"

_Note: these scripts are written for Python 3.x and ArcPy with associated Python 3 bindings.  To use them, you will have to have ArcPro 2.x installed on your computer and point your Python IDE towards ArcPy.  See notes in scripts.

## The hypothetical public health scenario: ##

*"The citizens and government in Middlesex County, Massachusetts are concerned by the recent discovery of a dead bird carrying West Nile Virus. The bird is believed to have lived in the local habitat, and the Centers for Disease Control (CDC) is considering whether to spray the surrounding are with a pesticide aimed at eliminating mosquitoes that may have contracted the disease. A representative from The CDC has arrived at your GIS lab and is asking you to help her evaluate whether or not CDCs current criteria for spraying a pesticide to eliminate the mosquitoes that carry the virus are likely to be effective. She has provided the spraying criteria below.*

*The Spraying Criteria: According to the CDC’s current criteria, spraying a pesticide by trucks must occur within a 2 kilometer radius around the site of any animal that has been found dead of the virus. However, it is known that pesticides sprayed by truck will only reach to 50 m on either side of roads. Further, the Environmental Protection Agency (EPA) has regulated that spraying must not occur within 100 m of any wetland because they don’t want to harm wetland biota."*

The parameterized scripts included in this repository are for a scaled-up version of this scenario for a statewide response. The scripts are written to handle thousands of data points received from an open reporting system from crowdsourced data: one point shapefile per each dead bird (yikes!).

The output of the script is a polygon feature class of buffers around roads that are within 2km of each reported dead bird, but not within 100 m of a wetland, showing the state where they can spray.

The general processing workflow to solve for this issue is relatively simple:

1. Deal with all the point shapefiles (See 'Shapefile Iterator' section below):
    1. Iterate through all of the single point shapefiles:
    2. Append each poiny to a newly created point featurelayer hosted in RAM
    3. Buffer 2km around each dead bird point feature 
    4. Dissolve the buffers
    5. Repair the buffer geometry.
2. Clip Roads, Wetland layers by above 2km buffers
3. Buffer these clipped roads & wetland layers
4. Erase clipped wetland buffers from road buffers using Erase tool.
5. Output of script is: road buffers, minus wetland buffered area, within 2km radius of dead bird
6. Calculate and return land area and percentage of land so the state knows how much pesticide to buy (ick):
    1. Iterate through result feature class of road-buffers-minus-wetland-buffers and sum up area of all features
    2. Iterate through all 2km buffer features around each dead bird and sum up area of all features
    3. Divide area of resulting feature class by area of 2km bird buffer to get percentage of area defined by 2km radius around each bird
    4. Print out in print() statement / arcpy.AddMessage()


## Performance Bottlenecks and solutions: ##

- Reducing XY resolution and tolerance to 0.01 in environment settings (didn’t have much of an effect but hypothetically still good to do)
-	Utilizing in-memory workspace for temporary layers used intermediate geoprocessing steps: RAM is a lot faster than disk I/O, even with an nvme SSD.
-	Dissolving all the buffers before using them in subsequent geoprocessing tasks, so that ArcPy wasn’t iterating through thousands of features later in the script.
-	The main bottleneck was the performance of the Clip tool and the fact that I was using it several times in the script. I used it early on to clip the roads and wetlands layers to the 2km buffer around each point, under the logic that buffering those layers would mean a smaller dataset for the subsequent buffer tool to work with. The issue is the Clip tool is slow, presumably due to it having to load an entire layer to memory and crack ALL THE FEATURES to the clip geometry.
-	Instead of clipping roads and wetlands prior to buffering, I used SelectLayerByLocation (i..e., Select by Geometry) to retrieve features in the roads and wetlands layers that intersected the 2km buffer around points. This dramatically improved performance.  I didn’t have time to research, but my guess is the underlying code for this tool utilizes SQL instead of cracking / reading / writing features so it’s just a straight read function as opposed to a more intensive geoprocessing function like Clip.
-	Only using Clip once, on the results of the Erase tool, at the end of the script.
-	Changing the script to run from the command line instead of from ArcPro. By most reports this speeds things up considerably since ArcPro / ArcMap’s (and Python IDE’s) traceback functions add a considerable amount of overhead.

## Source Data: ##

_These scripts were written to handle (outdated) data provided with the lab exercise itself. Data currently available at the links below may be slightly different, and scripts may need to be altered slightly to process them._

- MassDOT Roads: https://www.mass.gov/info-details/massgis-data-massachusetts-department-of-transportation-massdot-roads
- MassDEP Wetlands: https://www.mass.gov/info-details/massgis-data-massdep-wetlands-2005
- Zipped folder with 1000 shapefiles. Each containing a single point location somewhere in the state of Massachusetts, USA.

## Fixing errors with source data ##

- Wetlands layer’s geometry had a lot of self-overlapping polygons. Needed to be repaired as this caused problems with 1000 bird scenario
- Stripping roads and wetland layers of attribute fields that weren’t needed, to cut down on read-time.
- I wrote a script to do both of these, included in this file: deadbird_dataprep.py

## Errors with intermediate geoprocessing layers: ##

Even with this, my script still threw an “Invalid Topology [Incomplete void poly.]” error when running the Erase Tool.  I presume this is because the buffer tools, albeit well intentioned, were creating bad geometry and weird void polygons (like under minimum  XY tolerance or something. I had originally written this script with the buffer outputs all being dissolved into one gigantic multipart feature. I turned off dissolve on the buffer outputs of the roads and wetlands layers and added a RepairGeometry() after each buffering step.  This dramatically increased script runtime, with roads taking 7-8 minutes to repair the geometry and wetlands taking 3-5 minutes to repair.  But the script completes without error this way. 

## Shapefile Iterator ##

To deal with multiple shapefiles, my initial thought was to just merge them all. Several folks on Stack Exchange, however, reported that creating a blank featureLayer, iterating through the list of shapefiles, and using the Append tool, made fora much faster script.  


