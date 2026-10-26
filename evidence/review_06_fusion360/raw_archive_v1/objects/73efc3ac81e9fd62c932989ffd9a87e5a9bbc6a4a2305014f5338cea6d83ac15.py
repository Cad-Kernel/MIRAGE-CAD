import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-100))
r=w0.sketch().segment((12,10),(14,1)).arc((13,5),(12,10)).assemble().finalize().extrude(173).union(w0.sketch().segment((-14,5),(2,5)).segment((3,-11)).segment((10,-11)).segment((10,5)).segment((11,5)).segment((11,10)).segment((-14,10)).close().assemble().finalize().extrude(200))