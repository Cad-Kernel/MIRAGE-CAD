import cadquery as cq
w0=cq.Workplane('YZ',origin=(-2,0,0))
r=w0.sketch().segment((-100,-5),(100,-5)).segment((100,0)).segment((97,0)).arc((94,4),(91,0)).segment((-100,0)).close().assemble().finalize().extrude(4)