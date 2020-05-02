#!/usr/bin/python3
# This is a script that fixes the keys in an excel file so that tables can be joined.
# Note on nameing convention: _src_ refers to the source table for the _join_.  _dest_   
#   refers to the table database. This program fixes the source table.
# These values need to be set.
#   destJoinFn - The excel file that represents data to be joined to
#   destJoinSn - The excel sheet name (or number) for destJoinFn. 0 for default.
#   srcJoinFn - The excel file the represents data to be joined from
#   srcJoinSn - The excel sheet name (or number) for srcJoinFn. 0 for default
#   outFn - The output file name
#   srcMatchCol - The column to match from the srcJoinFn.  This likely will have data that needs to get fixed
#   destMatchCol - The column to match from the destJoinFn.  This contains data to match with srcMatchCol 
#   joinCol - The key data in the srcJoinFn that gets added to destJoinFn
#   orphans - Dictionary of fixes for unmatched data between files in form  {srcMatchCol[x] : joinCol[x], ... }
#   

import pandas as pd
from pandas import ExcelWriter, ExcelFile
import string
import os

#Set These
destJoinFn='./tl_2019_us_state.xlsx'
destJoinSn=0
srcJoinFn='./nst-est2019-01.xlsx'
srcJoinSn=0
outFn='./usPopEst2019.xlsx'
destMatchCol='NAME,C,100'  
srcMatchCol='Geographic Area'  
joinCol='NAME,C,100'
orphans={}

#The spreadsheet labels are weird, and I just want 2019
srcJoinDf=pd.read_excel(srcJoinFn, 
                        sheet_name=srcJoinSn, 
                        skiprows=[0,1,2,3], 
                        usecols="A,M", 
                        names=["Geographic Area", "2019"])

destJoinDf=pd.read_excel(destJoinFn, sheet_name=destJoinSn)

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
    
    #This is added because main problem is a leading period in excel.
    if destJoinRow.empty:
        srcNotInDest.append(item)
        try:
            destJoinRow=destJoinDf.loc[destJoinDf[destMatchCol] == item.lstrip('.')]
        #Some of the data isn't text. Just pass.
        except AttributeError:
            pass

    if destJoinRow.empty:
        try:
            srcFixCol.append(orphans[item])
        except KeyError: 
            print("Not adding %s to %s" % (item, joinCol))
            srcFixCol.append(None)
    else:
        srcFixCol.append(destJoinRow.iloc[0][joinCol])

destNotInSrc.sort()
print("\nIn dest, but not src\n", destNotInSrc)

#srcNotInDest.sort()
print("\nIn src, but not dest\n", srcNotInDest)

print("\nFixed data for src\n", srcFixCol)
srcJoinDf[joinCol]=srcFixCol

#Could do a join here, but am prepping dest do this in ArcGIS Pro
print("\nFixed Keys!  Writing dest file ",outFn)
srcJoinDf.to_excel(outFn, sheet_name=sheetName)


