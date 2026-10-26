import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-8))
w1=cq.Workplane('ZX',origin=(0,0,0))
r=w0.sketch().segment((-80,-37),(-15,-100)).segment((-6,-91)).segment((-6,-92)).segment((15,-100)).segment((80,-36)).segment((15,19)).segment((6,10)).segment((6,11)).segment((-15,19)).close().assemble().reset().face(w0.sketch().segment((-61,-36),(4,-96)).segment((61,-36)).segment((-4,24)).close().assemble(),mode='s').finalize().extrude(16).union(w1.workplane(offset=100/2).cylinder(100,11))