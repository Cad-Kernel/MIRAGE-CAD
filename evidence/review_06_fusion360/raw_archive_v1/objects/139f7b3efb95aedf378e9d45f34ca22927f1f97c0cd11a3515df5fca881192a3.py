import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,1,0))
r=w0.sketch().segment((-100,-56),(100,-28)).segment((100,28)).segment((-100,56)).close().assemble().finalize().extrude(-2)