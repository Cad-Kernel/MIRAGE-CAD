import cadquery as cq
w0=cq.Workplane('YZ',origin=(1,0,0))
r=w0.workplane(offset=-2/2).cylinder(2,100)