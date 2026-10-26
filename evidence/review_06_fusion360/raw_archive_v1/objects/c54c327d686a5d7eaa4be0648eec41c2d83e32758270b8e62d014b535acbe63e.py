import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,82,0))
r=w0.workplane(offset=-182/2).cylinder(182,27).union(w0.workplane(offset=18/2).cylinder(18,41))