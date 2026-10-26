import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,28,0))
r=w0.workplane(offset=-111/2).cylinder(111,11).union(w0.workplane(offset=55/2).cylinder(55,100))