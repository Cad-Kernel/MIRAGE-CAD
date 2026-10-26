import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-100))
r=w0.sketch().segment((-80,-78),(-63,-93)).segment((80,78)).segment((63,93)).close().assemble().finalize().extrude(200)