import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,50))
r=w0.workplane(offset=-100/2).cylinder(100,80).union(w0.workplane(offset=-20/2).cylinder(20,100))