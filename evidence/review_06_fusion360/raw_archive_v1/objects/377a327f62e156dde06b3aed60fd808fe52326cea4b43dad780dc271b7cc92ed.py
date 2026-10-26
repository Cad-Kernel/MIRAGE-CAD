import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-31,0))
w1=cq.Workplane('ZX',origin=(0,-32,0))
r=w0.workplane(offset=62/2).cylinder(62,87).union(w1.workplane(offset=50/2).cylinder(50,100))