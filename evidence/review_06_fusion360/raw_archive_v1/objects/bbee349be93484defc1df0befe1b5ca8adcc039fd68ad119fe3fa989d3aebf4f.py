import cadquery as cq
w0=cq.Workplane('YZ',origin=(100,0,0))
r=w0.sketch().arc((-3,-8),(0,-10),(3,-8)).segment((3,8)).arc((0,10),(-3,8)).close().assemble().finalize().extrude(-200)