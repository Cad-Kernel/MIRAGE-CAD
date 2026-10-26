import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,10,0))
r=w0.sketch().segment((-100,1),(0,-100)).segment((100,-1)).segment((0,100)).close().assemble().finalize().extrude(-21)