import cadquery as cq
w0=cq.Workplane('YZ',origin=(100,0,0))
r=w0.sketch().circle(12).rect(2,24,mode='s').finalize().extrude(-200)