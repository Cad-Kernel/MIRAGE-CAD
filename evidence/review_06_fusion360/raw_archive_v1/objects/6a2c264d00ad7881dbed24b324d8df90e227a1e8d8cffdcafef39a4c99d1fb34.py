import cadquery as cq
w0=cq.Workplane('YZ',origin=(81,0,0))
r=w0.workplane(offset=-162/2).cylinder(162,100)