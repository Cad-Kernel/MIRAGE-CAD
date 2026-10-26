import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,64,0))
r=w0.workplane(offset=-128/2).cylinder(128,100)