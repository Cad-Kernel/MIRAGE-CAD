import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,52,0))
w1=cq.Workplane('ZX',origin=(0,100,0))
r=w0.workplane(offset=-152/2).cylinder(152,14).union(w0.sketch().segment((-28,-3),(-12,-25)).segment((-8,-22)).segment((-8,-25)).segment((8,-24)).segment((8,-16)).segment((28,3)).segment((12,25)).segment((8,22)).segment((8,25)).segment((-8,24)).segment((-8,16)).close().assemble().finalize().extrude(-97)).union(w1.workplane(offset=-145/2).cylinder(145,14))