import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-73))
r=w0.workplane(offset=-27/2).cylinder(27,67).union(w0.workplane(offset=173/2).cylinder(173,40))