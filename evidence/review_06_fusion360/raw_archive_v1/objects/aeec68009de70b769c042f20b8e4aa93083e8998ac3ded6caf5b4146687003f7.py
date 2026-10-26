import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,36))
r=w0.sketch().push([(-4,0)]).circle(96).reset().face(w0.sketch().segment((64,75),(85,40)).segment((100,84)).segment((94,91)).close().assemble()).finalize().extrude(-72)