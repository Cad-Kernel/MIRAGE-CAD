import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-19,0))
w1=cq.Workplane('ZX',origin=(0,19,0))
r=w0.workplane(offset=8/2).moveTo(6.5,35.5).box(103,129,8).union(w0.workplane(offset=8/2).moveTo(-49.5,-89.5).box(17,21,8)).union(w1.sketch().segment((-41,-25),(54,-25)).segment((54,96)).segment((41,96)).segment((41,83)).segment((45,83)).segment((45,64)).segment((41,64)).segment((41,-14)).segment((-28,-14)).segment((-28,64)).segment((-32,64)).segment((-32,83)).segment((-28,83)).segment((-28,96)).segment((-41,96)).close().assemble().finalize().extrude(-34))