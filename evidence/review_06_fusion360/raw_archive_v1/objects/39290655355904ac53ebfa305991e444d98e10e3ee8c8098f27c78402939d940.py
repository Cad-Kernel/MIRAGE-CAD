import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-56))
r=w0.sketch().segment((-100,-7),(100,-7)).segment((100,7)).segment((-29,7)).arc((-35,3),(-41,7)).segment((-100,7)).close().assemble().push([(-89,3)]).circle(7,mode='s').push([(91,1)]).circle(6,mode='s').finalize().extrude(112)