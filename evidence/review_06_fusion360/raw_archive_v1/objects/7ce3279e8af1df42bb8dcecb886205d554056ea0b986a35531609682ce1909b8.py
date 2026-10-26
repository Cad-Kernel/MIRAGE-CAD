import cadquery as cq
w0=cq.Workplane('YZ',origin=(53,0,0))
r=w0.sketch().segment((-87,-49),(0,-100)).segment((8,-90)).segment((87,-50)).segment((87,50)).segment((0,100)).segment((-87,49)).close().assemble().finalize().extrude(-107)