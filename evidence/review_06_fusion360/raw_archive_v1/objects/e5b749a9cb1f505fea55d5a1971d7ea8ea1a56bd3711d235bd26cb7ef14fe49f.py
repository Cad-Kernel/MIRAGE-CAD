import cadquery as cq
w0=cq.Workplane('YZ',origin=(-14,0,0))
w1=cq.Workplane('YZ',origin=(-71,0,0))
r=w0.sketch().circle(57).push([(-1,0)]).circle(28,mode='s').finalize().extrude(-29).union(w0.workplane(offset=114/2).cylinder(114,98)).union(w1.sketch().circle(57).rect(56,56,mode='s').finalize().extrude(-29))