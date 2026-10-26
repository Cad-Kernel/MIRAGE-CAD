import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-5,0))
r=w0.sketch().segment((-59,58),(-47,34)).segment((-1,49)).arc((49,72),(-5,87)).close().assemble().push([(18,68)]).circle(23,mode='s').reset().face(w0.sketch().segment((-55,-44),(-24,-64)).arc((55,-87),(1,-39)).segment((-48,-23)).close().assemble()).push([(16,-68)]).circle(21,mode='s').finalize().extrude(10)