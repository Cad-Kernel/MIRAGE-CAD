import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,30))
r=w0.workplane(offset=-130/2).cylinder(130,28).union(w0.workplane(offset=70/2).cylinder(70,20))