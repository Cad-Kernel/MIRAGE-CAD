import cadquery as cq
w0=cq.Workplane('YZ',origin=(23,0,0))
r=w0.sketch().segment((-15,-86),(100,-86)).segment((100,86)).segment((-15,86)).segment((-15,85)).arc((-100,0),(-15,-85)).close().assemble().push([(-14,0)]).circle(37,mode='s').finalize().extrude(-46)