import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,17,0))
r=w0.sketch().segment((-71,-100),(29,-100)).segment((71,-11)).arc((63,47),(29,100)).segment((-71,100)).close().assemble().finalize().extrude(-34)