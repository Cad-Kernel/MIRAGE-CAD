import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-3,0))
r=w0.sketch().circle(100).circle(96,mode='s').finalize().extrude(6)