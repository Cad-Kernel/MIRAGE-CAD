import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-2))
r=w0.sketch().circle(100).circle(24,mode='s').finalize().extrude(4)