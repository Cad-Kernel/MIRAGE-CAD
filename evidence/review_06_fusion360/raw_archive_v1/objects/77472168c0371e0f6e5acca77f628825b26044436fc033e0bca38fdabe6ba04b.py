import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-5))
r=w0.sketch().circle(100).circle(83,mode='s').finalize().extrude(-10).union(w0.sketch().circle(83).circle(67,mode='s').finalize().extrude(20))