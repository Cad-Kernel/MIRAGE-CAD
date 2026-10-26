import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-4))
r=w0.workplane(offset=5/2).moveTo(-84,0).cylinder(5,10).union(w0.sketch().push([(-85,0)]).circle(15).push([(-84,0)]).circle(8,mode='s').push([(84,0)]).circle(16).reset().face(w0.sketch().segment((77,0),(86,-4)).segment((92,5)).segment((83,9)).close().assemble(),mode='s').finalize().extrude(8))