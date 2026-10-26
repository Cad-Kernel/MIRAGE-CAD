import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,41))
r=w0.workplane(offset=-140/2).cylinder(140,23).union(w0.workplane(offset=-41/2).cylinder(41,100)).union(w0.workplane(offset=58/2).cylinder(58,23))