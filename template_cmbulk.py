
def umfi_idle(bsc: str, gsmcell: str, umfiidle: str) -> str:
    return f"""SET
FDN:SubNetwork={bsc},SubNetwork={bsc},MeContext={bsc},ManagedElement={bsc},BscFunction=1,BscM=1,GeranCellM=1,GeranCell={gsmcell},Mobility=1,InterRanMobility=1
umfiIdleList : [{umfiidle}] 
"""

def Add_InternalUtranRelation(rnc: str, sourcecell: str, targetcell: str, loadsharing: str, qoffset2sn: str, selectionprio: str) -> str:
    return f"""CREATE
FDN : SubNetwork={rnc},MeContext={rnc},ManagedElement=1,BSCFunction=1,UtranCell={sourcecell},UtranRelation={targetcell}
utranCellRef : "SubNetwork={rnc},MeContext={rnc},ManagedElement=1,BSCFunction=1,UtranCell={targetcell}"
hcsSib11Config : {{hcsPrio=0, qHcs=0, penaltyTime=0, temporaryOffset1=0, temporaryOffset2=0}}
loadSharingCandidate : {loadsharing}
qOffset1sn : 0
qOffset2sn : {qoffset2sn}
selectionPriority : {selectionprio}"""