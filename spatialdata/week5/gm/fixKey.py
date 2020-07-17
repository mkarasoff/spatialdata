#!/usr/bin/python3
# This is a script that fixes the keys in an excel file so that tables can be joined.
import pandas as pd
from pandas import ExcelWriter, ExcelFile
import string
import os

#Set These##############################################################################
destJoinFn='./UIA_World_Countries_Boundaries.xlsx'
destJoinSn=0
srcJoinFn='./eg_elc_rnew_zs.xlsx'
srcJoinSn=0
outFn='./renewable_use.xlsx'
destMatchCol='COUNTRY,C,40'  
srcMatchCol='country'  
joinCol='ISO,C,2'
orphans={'Brunei' : 'BN', \
        'Congo, Dem. Rep.' : 'CD', \
        'Congo, Rep.' : 'CG', \
        "Cote d'Ivoire" : 'CI', \
        'Kyrgyz Republic' : 'KG', \
        'Russia' : 'RU', \
        'Slovak Republic' : 'SK',\
        'Lao' : 'LA', \
        'Micronesia, Fed. Sts.' : 'FM', \
        'Palestine' : 'PS', \
        'Cape Verde' : 'CV', \
        'St. Kitts and Nevis' : 'KN', \
        'St. Lucia' : 'LC', \
        'St. Vincent and the Grenadines' : 'VC', \
        'Swaziland' : 'SZ', \
        }
#############################################################################################


destJoinDf=pd.read_excel(destJoinFn, sheet_name=destJoinSn)
srcJoinDf=pd.read_excel(srcJoinFn, sheet_name=srcJoinSn)
sheetName=os.path.splitext(os.path.basename(outFn))[0]

print("Join Dest Cols:")
print(destJoinDf.columns)

print("Join Src Cols:")
print(srcJoinDf.columns)

print("Using orphans:")
print(orphans)

srcFixCol=[]
srcNotInDest=[]
destNotInSrc=[c for c in list(destJoinDf[destMatchCol]) if c not in list(srcJoinDf[srcMatchCol])] 

for item in list(srcJoinDf[srcMatchCol]):
    destJoinRow=destJoinDf.loc[destJoinDf[destMatchCol] == item]
    
    if destJoinRow.empty:
        srcNotInDest.append(item)
        try:
            srcFixCol.append(orphans[item])
        except KeyError: 
            print("Not adding %s to %s" % (item, joinCol))
            srcFixCol.append(None)
    else:
        srcFixCol.append(destJoinRow.iloc[0][joinCol])

destNotInSrc.sort()
print("\nIn dest, but not src\n", destNotInSrc)

srcNotInDest.sort()
print("\nIn src, but not dest\n", srcNotInDest)

print("\nFixed data for src\n", srcFixCol)
srcJoinDf[joinCol]=srcFixCol

#Could do a join here, but am prepping dest do this in ArcGIS Pro
print("\nFixed Keys!  Writing dest file ",outFn)
srcJoinDf.to_excel(outFn, sheet_name=sheetName)
