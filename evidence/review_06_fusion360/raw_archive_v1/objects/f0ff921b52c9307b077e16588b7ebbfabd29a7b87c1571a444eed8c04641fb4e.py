import cadquery as cq
w0=cq.Workplane('YZ',origin=(6,0,0))
r=w0.sketch().circle(100).circle(94,mode='s').finalize().extrude(-12)