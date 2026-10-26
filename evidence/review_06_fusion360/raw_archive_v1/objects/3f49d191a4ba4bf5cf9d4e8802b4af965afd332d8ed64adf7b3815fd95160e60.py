import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-37,0))
r=w0.workplane(offset=-63/2).cylinder(63,11).union(w0.workplane(offset=137/2).cylinder(137,4))