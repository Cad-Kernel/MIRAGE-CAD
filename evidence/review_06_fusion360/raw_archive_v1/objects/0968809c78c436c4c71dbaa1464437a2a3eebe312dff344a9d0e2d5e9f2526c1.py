import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,100,0))
r=w0.sketch().segment((-6,-64),(6,-64)).segment((6,-54)).segment((-3,-55)).segment((-3,55)).segment((6,54)).segment((6,64)).segment((-6,64)).close().assemble().finalize().extrude(-200)