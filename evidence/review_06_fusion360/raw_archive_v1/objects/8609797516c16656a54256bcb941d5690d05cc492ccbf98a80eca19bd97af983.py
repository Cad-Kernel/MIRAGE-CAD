import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-6))
r=w0.sketch().circle(100).circle(63,mode='s').finalize().extrude(12)