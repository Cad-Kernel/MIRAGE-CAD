import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-41,0))
w1=cq.Workplane('YZ',origin=(-2,0,0))
r=w0.workplane(offset=106/2).moveTo(0,-22).cylinder(106,11).union(w0.sketch().push([(0,-22)]).circle(5).circle(3,mode='s').finalize().extrude(141)).union(w1.workplane(offset=35/2).moveTo(-41,0).cylinder(35,59))