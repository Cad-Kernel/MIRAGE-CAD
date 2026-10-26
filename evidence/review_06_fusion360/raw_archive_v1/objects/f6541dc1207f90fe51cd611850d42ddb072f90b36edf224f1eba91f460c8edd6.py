import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,18,0))
w1=cq.Workplane('YZ',origin=(-14,0,0))
r=w0.sketch().segment((-100,-36),(59,-86)).segment((62,-91)).segment((100,-91)).segment((100,-73)).segment((64,-73)).segment((-100,-18)).close().assemble().finalize().extrude(-36).union(w1.workplane(offset=105/2).moveTo(0,-82).cylinder(105,11))