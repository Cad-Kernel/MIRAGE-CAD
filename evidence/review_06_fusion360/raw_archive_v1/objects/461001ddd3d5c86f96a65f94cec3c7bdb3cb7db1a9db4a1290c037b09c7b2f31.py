import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,31,0))
w1=cq.Workplane('ZX',origin=(0,14,0))
r=w0.sketch().circle(100).circle(82,mode='s').finalize().extrude(-62).union(w0.sketch().circle(77).reset().face(w0.sketch().segment((-22,-46),(22,-46)).segment((22,-14)).arc((0,-24),(-22,-14)).close().assemble(),mode='s').reset().face(w0.sketch().arc((-22,14),(0,24),(22,14)).segment((22,46)).segment((-22,46)).close().assemble(),mode='s').finalize().extrude(-23)).union(w1.workplane(offset=-12/2).box(44,74,12))