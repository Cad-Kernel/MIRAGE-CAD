import cadquery as cq
w0=cq.Workplane('YZ',origin=(100,0,0))
r=w0.workplane(offset=-200/2).cylinder(200,4).union(w0.workplane(offset=-182/2).cylinder(182,6))