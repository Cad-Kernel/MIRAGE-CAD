import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,100,0))
r=w0.sketch().segment((-50,-29),(2,-58)).arc((25,-43),(50,-29)).segment((50,29)).segment((0,58)).arc((-25,43),(-50,29)).close().assemble().finalize().extrude(-200)