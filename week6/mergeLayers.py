import arcpy
import os
import re
import sys

try:
    arcpy.env.workspace = os.environ['ARCDBPATH']
except KeyError:
    pass

#For the sake of sanity
print(arcpy.env.workspace)

layerCfgs = {
    'UnsuitableAreas': 
        ['AirportCompatibilityZoneA', 'PrimeFarmland', 'MeadowfoamPreserve', 'CriticalHabitat', 'TribalLands',
         'Waterbodies', 'State_Federal_TribalLands', 'UrbanResidentialZones', 'ButteCountyBoundary'],
    'Farmland': 
        ['GrazingLands', 'PrimeFarmland', 'ButteCountyBoundary'],
    'ConstrainedAreas':
        ['Williamson_Act_Parcels',  'NonUrban_ResidentialParcels_Lessthan20Acres', 'Parcels_Industrial_CommercialUse',
         'AirportCompatibilityZones_BthroughD_Diss', 'ScenicHighwayOverlayZone',
         'OakWoodlands', 'DeerHerdOverlay', 'Wetlands_revised', 'FloodHazard_HundredYr', 'SevereErosionHazardAreas',
         'FireHazardZones_High_and_VeryHighZones', 'ButteCountyBoundary'],
    'GeneralPlan_Identified_ScenicHighways':
        ['GeneralPlan_Identified_ScenicHighways', 'ButteCountyBoundary'],
    'ResidentialProximity':
        ['ResidentialProximity', 'ButteCountyBoundary'],
    'ParcelSize':
        ['NonUrban_ResidentialParcels_Lessthan20Acres', 'residentialParcels_Greaterthan20acres', 
         'Williamson_Act_Parcels', 'ButteCountyBoundary'],
    'OpportunityAreas':
        ['UrbanPermitAreas', 'ToxicContaminants', 'SolidWasteManagementFacility_OverlayZone', 'Conservation_Easements', 'ButteCountyBoundary'],
    'OpportunityBuffers':
        ['TransmissionLines', 'Substations', 'ButteCountyBoundary']
}

def delLayers(layerCfgs):
    for layerName, featureNames in layerCfgs.items():
        for featureName in featureNames:
            arcpy.Delete_management(featureName)


def scratchLayers(layerCfgs):
    scratchLayerCfgs={}
    for layerName, featureNames in layerCfgs.items():
        newFeatureNames=[]
        for featureName in featureNames:
            scratchFeatureName='%s_%s'%(featureName, layerName)
            print("Scratch Feature Name", scratchFeatureName)
            arcpy.Delete_management(scratchFeatureName)
            arcpy.CopyFeatures_management(featureName, scratchFeatureName)
            newFeatureNames.append(scratchFeatureName)
        scratchLayerCfgs[layerName]=newFeatureNames
    return scratchLayerCfgs

def mergeLayers(layerCfgs):
    for layerName, featureNames in layerCfgs.items():
        print("Working on", layerName)
        addFeatureNames(layerName, featureNames)

        fixLayers(featureNames)

        mergeFeatures = ";".join(featureNames)

        arcpy.Delete_management(layerName)

        try:
            arcpy.management.Merge(mergeFeatures, layerName)
        except arcpy.ExecuteError:
            errMsg = arcpy.GetMessages(2)
            print(errMsg)
            if"ERROR 002948" in errMsg:
                print("Don't try to merge unlike items.")
                print(layerName, "Won't merge, continuing")
            else:
                raise

def fixLayers(featureSet):

    featureFields={}
    for feature in featureSet:
        featureFields[feature] = arcpy.ListFields(feature)

    #fixSpacedNone(featureFields)
    #print("SpacedNone Done")

    print("Looking for type mismathes")
    typeMismatches = findTypeMismatches(featureFields)

    if len(typeMismatches) > 0:
        print("Type Matches found")
        print(typeMismatches)

        fixTypeMismatches(featureFields, typeMismatches)

    return typeMismatches


def findTypeMismatches(featureFields, featureNames=None, fixIt=set()):

    ignoreMatch = ['FeatureName', 'OBJECTID', 'Shape', 'Shape_Area', 'Shape_Length']

    if featureNames is None:
        featureNames = list(featureFields.keys())

    testFieldTypes = {field.name: field.type for field in featureFields[featureNames[0]]}
    del featureNames[0]

    for matchFeatureName in featureNames:
        matchFieldTypes = {field.name: field.type for field in featureFields[matchFeatureName]}

        matches = list(set(matchFieldTypes.keys()) & set(testFieldTypes.keys()))

        typeMismtatch = [match for match in matches if match not in ignoreMatch \
                         and matchFieldTypes[match] != testFieldTypes[match]]

        fixIt = fixIt | set(typeMismtatch)

    if len(featureNames) <= 1:
        return fixIt
    else:
        return findTypeMismatches(featureFields, featureNames, fixIt)


def fixTypeMismatches(featureFields, typeMismatches):

    for featureName, fields in featureFields.items():
        namedFields = {field.name: field for field in fields}
        fixFields = set(namedFields.keys()) & set(typeMismatches)

        for fieldName in fixFields:
            newFieldName="%s_%s" % (fieldName, featureName)

            print("Rename field", fieldName, "in", featureName, "to", newFieldName)
            arcpy.management.AlterField(featureName, fieldName,
                                        new_field_name=newFieldName[:31])

#This will replace values that are just spaces, like ' ', with Null values.  For some reason, such values trip up
# merges.
def fixSpacedNone(featureFields):
    for featureName, fields in featureFields.items():

        fieldNames = list(map(lambda x: x.name, fields))

        #Check for empty fields and fix
        with arcpy.da.UpdateCursor(featureName, fieldNames) as cursor:
           for row in cursor:
                if ' ' in row:
                    fixedRow = [ None if item == ' ' else item for item in row ]
                    print("SpacedNone Row")
                    print(row)
                    print(fixedRow)

                    cursor.updateRow(fixedRow)

def addFeatureNames(layerName, featureNames):
    for featureName in featureNames:
        print("Stripping", layerName, "From", featureName)

        fieldVal='\"%s\"'% (re.sub('_' + layerName + '$', '', featureName))
        print("Adding Feature Name", fieldVal)

        arcpy.management.AddField(featureName, 'FeatureName', 'TEXT', 64)
        arcpy.management.CalculateField(featureName, 'FeatureName', fieldVal)

def modMergedField(featureName, modFeatureName, fieldName, value):
    searchFields=["featureName", fieldName]
    print(searchFields)

    with arcpy.da.UpdateCursor(featureName, searchFields) as cursor:
        for row in cursor:
            if row[0] == modFeatureName:
                updateRow=[row[0], value]
                print("Fixing Row", fieldName)
                cursor.updateRow(updateRow)

workingLayersCfg = scratchLayers(layerCfgs)
mergeLayers(workingLayersCfg)
delLayers(workingLayersCfg)

#This adds data for the rasture fields that will be used.
modMergedField('ParcelSize', 'ButteCountyBoundary', 'ACRES', 0)
modMergedField('ResidentialProximity', 'ButteCountyBoundary', 'DistRange', '4000 plus')




