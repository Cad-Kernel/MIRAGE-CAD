import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,11,0))
r=w0.sketch().circle(100).circle(44,mode='s').finalize().extrude(-22)