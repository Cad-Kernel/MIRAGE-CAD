import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,93))
r=w0.sketch().segment((-100,-54),(-46,-54)).arc((-35,-65),(-23,-76)).segment((23,-76)).arc((35,-65),(46,-54)).segment((100,-54)).segment((100,76)).segment((-100,76)).close().assemble().push([(0,-2)]).circle(37,mode='s').finalize().extrude(-186)