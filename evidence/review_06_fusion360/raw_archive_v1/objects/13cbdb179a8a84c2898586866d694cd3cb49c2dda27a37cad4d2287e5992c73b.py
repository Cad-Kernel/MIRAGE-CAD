import cadquery as cq
w0=cq.Workplane('YZ',origin=(15,0,0))
r=w0.sketch().circle(100).circle(69,mode='s').finalize().extrude(-30)