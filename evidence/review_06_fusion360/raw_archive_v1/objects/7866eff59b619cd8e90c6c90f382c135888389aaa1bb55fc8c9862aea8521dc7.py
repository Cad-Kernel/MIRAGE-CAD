import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,100,0))
r=w0.sketch().arc((-53,-59),(-1,-79),(53,-59)).segment((53,59)).arc((-1,80),(-53,59)).close().assemble().finalize().extrude(-200)