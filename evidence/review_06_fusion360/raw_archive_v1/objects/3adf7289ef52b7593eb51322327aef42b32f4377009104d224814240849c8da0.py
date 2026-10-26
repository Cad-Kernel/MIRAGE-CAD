import cadquery as cq
w0=cq.Workplane('YZ',origin=(-2,0,0))
r=w0.workplane(offset=-98/2).cylinder(98,13).union(w0.workplane(offset=102/2).cylinder(102,18))