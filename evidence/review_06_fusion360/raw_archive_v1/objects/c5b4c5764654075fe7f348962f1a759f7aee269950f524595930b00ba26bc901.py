import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,40))
r=w0.workplane(offset=-80/2).cylinder(80,100)