import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-1))
r=w0.sketch().circle(100).circle(71,mode='s').finalize().extrude(2)