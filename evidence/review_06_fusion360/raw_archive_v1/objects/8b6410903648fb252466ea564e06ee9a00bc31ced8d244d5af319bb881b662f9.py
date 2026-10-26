import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,10,0))
r=w0.sketch().segment((-36,-67),(0,-67)).segment((0,-100)).segment((36,-100)).segment((36,100)).segment((0,100)).segment((0,67)).segment((-36,67)).close().assemble().finalize().extrude(-20)