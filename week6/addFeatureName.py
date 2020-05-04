import arcpy
dbPath="%s\\"%(arcpy.env.workspace)

vects=arcpy.ListFeatureClasses('*')

for vect in vects:
    arcpy.management.AddField(vect, 'FeatureName', 'TEXT', 64)
    arcpy.management.CalculateField(vect, 'FeatureName', 'vect')

    arcpy.management

