
def umfi_idle(bsc: str, gsmcell: str, umfiidle: str) -> str:
    return f"""SET
FDN:SubNetwork={bsc},SubNetwork={bsc},MeContext={bsc},ManagedElement={bsc},BscFunction=1,BscM=1,GeranCellM=1,GeranCell={gsmcell},Mobility=1,InterRanMobility=1
umfiIdleList : [{umfiidle}] 
"""
