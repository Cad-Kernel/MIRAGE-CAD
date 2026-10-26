import cadquery as cq
w0=cq.Workplane('YZ',origin=(5,0,0))
r=w0.workplane(offset=-20/2).moveTo(-8,-50).cylinder(20,2).union(w0.sketch().segment((-13,-100),(13,-100)).segment((13,-90)).segment((-3,-90)).segment((-3,90)).segment((13,90)).segment((13,100)).segment((-13,100)).close().assemble().finalize().extrude(10))