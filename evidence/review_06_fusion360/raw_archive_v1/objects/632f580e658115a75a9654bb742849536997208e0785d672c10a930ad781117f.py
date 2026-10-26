import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,23))
r=w0.sketch().segment((-100,-77),(100,-77)).arc((67,-44),(36,-13)).segment((36,77)).segment((-100,77)).close().assemble().push([(-32,9)]).circle(23,mode='s').finalize().extrude(-46)