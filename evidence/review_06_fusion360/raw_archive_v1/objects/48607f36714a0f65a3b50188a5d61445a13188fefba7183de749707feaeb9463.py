import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,13))
w1=cq.Workplane('YZ',origin=(-13,0,0))
r=w0.sketch().segment((-33,0),(33,0)).segment((33,73)).segment((31,73)).arc((-1,100),(-33,73)).close().assemble().push([(0,66)]).circle(17,mode='s').finalize().extrude(20).union(w1.sketch().segment((-75,-33),(0,-33)).segment((0,33)).segment((-75,33)).segment((-75,31)).arc((-100,0),(-75,-32)).close().assemble().push([(-67,0)]).circle(17,mode='s').finalize().extrude(26))