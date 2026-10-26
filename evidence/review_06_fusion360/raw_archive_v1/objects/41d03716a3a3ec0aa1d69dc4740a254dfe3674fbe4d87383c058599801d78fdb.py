import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().circle(100).circle(59,mode='s').finalize().extrude(28)