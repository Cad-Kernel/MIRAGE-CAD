import cadquery as cq
w0=cq.Workplane('YZ',origin=(-6,0,0))
r=w0.sketch().segment((-100,-6),(100,-6)).segment((100,2)).arc((97,4),(97,6)).segment((-100,6)).close().assemble().finalize().extrude(12)