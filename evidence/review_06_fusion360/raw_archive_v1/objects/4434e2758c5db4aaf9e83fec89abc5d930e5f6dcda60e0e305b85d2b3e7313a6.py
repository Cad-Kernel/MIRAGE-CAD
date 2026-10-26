import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-25))
w1=cq.Workplane('XY',origin=(0,0,-27))
r=w0.workplane(offset=13/2).cylinder(13,100).union(w1.workplane(offset=54/2).cylinder(54,67))