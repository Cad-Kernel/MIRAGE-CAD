import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,6,0))
r=w0.sketch().segment((-100,-20),(100,-20)).segment((63,20)).close().assemble().finalize().extrude(-12)