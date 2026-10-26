import cadquery as cq
w0=cq.Workplane('YZ',origin=(-100,0,0))
r=w0.sketch().segment((-2,-18),(2,-18)).segment((2,18)).segment((-2,18)).segment((-2,14)).segment((0,14)).segment((0,9)).segment((-2,9)).close().assemble().push([(-0.5,-12)]).rect(3,4,mode='s').push([(0.5,5)]).rect(3,2,mode='s').push([(0.5,-1.5)]).rect(3,3,mode='s').finalize().extrude(200)