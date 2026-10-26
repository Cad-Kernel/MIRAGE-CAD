import cadquery as cq
w0=cq.Workplane('YZ',origin=(38,0,0))
w1=cq.Workplane('YZ',origin=(50,0,0))
r=w0.workplane(offset=-101/2).cylinder(101,12).union(w0.sketch().circle(100).rect(190,50,mode='s').finalize().extrude(24)).union(w1.workplane(offset=-10/2).cylinder(10,97))