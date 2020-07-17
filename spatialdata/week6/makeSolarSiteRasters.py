import arcpy
import arcpy
import os
import sys

try:
    arcpy.env.workspace = os.environ['ARCDBPATH']
except KeyError:
    pass

#This generates rasters from the merged features.  The buffers are also generated as separate raters.
rasterList = [
    ('UnsuitableAreas', 'UnsuitableAreasRaster', 'FeatureName'),
    ('ConstrainedAreas', 'ConstrainedAreasRaster', 'FeatureName'),
    ('Farmland', 'FarmlandRaster', 'FeatureName'),
    ('OpportunityAreas', 'OpportunityAreasRaster', 'FeatureName'),
    ('ParcelSize', 'ParcelSizeRaster', 'ACRES'),
    ('TransmissionLines', 'TransmissionLinesRaster', 'DEST_SUB'),
    ('Substations', 'SubstationsRaster', 'SUB_NAME'),
    ('ResidentialProximity', 'ResidentialProximityRaster', 'DistRange'),
    ('GeneralPlan_Identified_ScenicHighways', 'GeneralPlan_Identified_ScenicHighwaysRaster', 'FeatureName')]


for raster in rasterList:
    print("Converting feature", raster[0], "to raster", raster[1])
    arcpy.Delete_management(raster[1])
    arcpy.conversion.FeatureToRaster(raster[0], raster[2], raster[1], 50)

