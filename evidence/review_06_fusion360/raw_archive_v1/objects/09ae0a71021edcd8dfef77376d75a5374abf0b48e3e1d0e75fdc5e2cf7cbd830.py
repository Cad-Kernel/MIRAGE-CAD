import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,60,0))
r=w0.sketch().circle(100).circle(50,mode='s').finalize().extrude(-120)