import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,70,0))
r=w0.sketch().push([(-70,1)]).circle(5).push([(0,-70)]).circle(5).push([(0,70)]).circle(5).push([(70,1)]).circle(5).finalize().extrude(-140).union(w0.workplane(offset=-20/2).cylinder(20,100))