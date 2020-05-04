import arcpy
import os
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
         'Waterbodies', 'State_Federal_TribalLands', 'UrbanResidentialZones'],
    'Farmland': 
        ['GrazingLands', 'PrimeFarmland'],
    'ConstrainedAreas':
        ['Williamson_Act_Parcels',  'NonUrban_ResidentialParcels_Lessthan20Acres', 'Parcels_Industrial_CommercialUse',
         'AirportCompatibilityZones_BthroughD_Diss', 'ScenicHighwayOverlayZone',
         'OakWoodlands', 'DeerHerdOverlay', 'Wetlands_revised', 'FloodHazard_HundredYr', 'SevereErosionHazardAreas',
         'FireHazardZones_High_and_VeryHighZones'],
    'ConstrainedBuffers':
        ['ResidentialProximity', 'GeneralPlan_Identified_ScenicHighways'],
    'ParcelSize':
        ['NonUrban_ResidentialParcels_Lessthan20Acres', 'residentialParcels_Greaterthan20acres', 
         'Williamson_Act_Parcels'],
    'OpportunityAreas':
        ['UrbanPermitAreas', 'ToxicContaminants', 'SolidWasteManagementFacility_OverlayZone', 'Conservation_Easements'],
    'OpportunityBuffers':
        ['TransmissionLines', 'Substations']
}

backGroundLayer = 'ButteCountyBoundary'

def mergeLayers(layerCfgs):
    addFeatureNames([backGroundLayer, ])
    for layerName, featureNames in layerCfgs.items():
        print("Working on", layerName)
        addFeatureNames(featureNames)
        fixLayers(featureNames)

        mergeFeatures = ";".join(featureNames)
        mergeFeatures = '%s;%s' % (mergeFeatures, backGroundLayer)

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

    fixSpacedNone(featureFields)
    print("SpacedNone Done")

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


def addFeatureNames(featureNames):
    for featureName in featureNames:
        print("Adding Feature Name", featureName)

        fieldVal='\"%s\"'%(featureName)
        arcpy.management.AddField(featureName, 'FeatureName', 'TEXT', 64)
        arcpy.management.CalculateField(featureName, 'FeatureName', fieldVal)



mergeLayers(layerCfgs)





