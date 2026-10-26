import cadquery as cq
w0=cq.Workplane('YZ',origin=(-12,0,0))
r=w0.sketch().circle(100).circle(93,mode='s').finalize().extrude(12).union(w0.sketch().circle(94).circle(88,mode='s').finalize().extrude(24))