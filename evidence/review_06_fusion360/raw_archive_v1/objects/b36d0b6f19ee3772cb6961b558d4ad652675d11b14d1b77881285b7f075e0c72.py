import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,13,0))
r=w0.sketch().segment((-100,-86),(-86,-86)).segment((-86,-100)).segment((86,-100)).segment((86,-86)).segment((100,-86)).segment((100,86)).segment((86,86)).segment((86,100)).segment((-86,100)).segment((-86,86)).segment((-100,86)).close().assemble().finalize().extrude(-26)