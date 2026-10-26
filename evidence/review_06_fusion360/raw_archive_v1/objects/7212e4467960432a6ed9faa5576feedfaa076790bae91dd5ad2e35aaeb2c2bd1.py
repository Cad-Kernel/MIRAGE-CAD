import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-8,0))
r=w0.sketch().circle(100).reset().face(w0.sketch().segment((-60,-72),(38,-72)).segment((38,-29)).arc((47,0),(38,29)).segment((38,72)).segment((-60,72)).segment((-60,29)).arc((-69,0),(-60,-29)).close().assemble(),mode='s').finalize().extrude(-11).union(w0.sketch().circle(89).circle(45,mode='s').finalize().extrude(27))