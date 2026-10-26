import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,34,0))
r=w0.sketch().segment((-100,0),(100,-61)).segment((100,61)).segment((-100,0)).assemble().finalize().extrude(-68)