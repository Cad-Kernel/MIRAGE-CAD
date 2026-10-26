import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,1,0))
r=w0.sketch().segment((-100,-23),(100,-23)).segment((100,15)).segment((20,15)).arc((17,20),(14,23)).segment((-47,23)).arc((-79,10),(-100,-20)).close().assemble().push([(58,-6)]).circle(10,mode='s').finalize().extrude(-3)