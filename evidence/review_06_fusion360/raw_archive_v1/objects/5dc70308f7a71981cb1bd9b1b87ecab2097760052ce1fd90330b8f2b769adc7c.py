import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,21,0))
r=w0.workplane(offset=-42/2).cylinder(42,100)