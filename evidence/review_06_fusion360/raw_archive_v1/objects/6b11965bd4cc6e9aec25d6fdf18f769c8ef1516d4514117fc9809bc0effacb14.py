import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,17))
r=w0.sketch().segment((92,-1),(100,-1)).segment((100,3)).segment((92,3)).arc((-100,0),(92,-1)).assemble().finalize().extrude(-34)