import cadquery as cq
w0=cq.Workplane('YZ',origin=(-100,0,0))
r=w0.sketch().segment((0,0),(0,0)).segment((0,1)).segment((0,0)).close().assemble().finalize().extrude(200)