import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-50,0))
r=w0.sketch().circle(100).circle(38,mode='s').finalize().extrude(100)