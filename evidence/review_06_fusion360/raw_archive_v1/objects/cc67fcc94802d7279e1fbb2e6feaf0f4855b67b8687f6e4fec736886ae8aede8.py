import cadquery as cq
w0=cq.Workplane('YZ',origin=(40,0,0))
r=w0.sketch().circle(100).circle(30,mode='s').finalize().extrude(-100).union(w0.sketch().circle(60).circle(30,mode='s').finalize().extrude(20))