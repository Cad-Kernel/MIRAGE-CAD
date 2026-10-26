import cadquery as cq
w0=cq.Workplane('YZ',origin=(60,0,0))
w1=cq.Workplane('XY',origin=(0,0,17))
r=w0.sketch().push([(7.5,0)]).rect(115,36).push([(87,0)]).circle(13).circle(10,mode='s').finalize().extrude(-120).union(w1.sketch().segment((-38,-94),(-35,-94)).segment((-35,-100)).segment((35,-100)).segment((35,-94)).segment((39,-94)).segment((39,-93)).segment((35,-93)).segment((35,-50)).segment((-35,-50)).segment((-35,-93)).segment((-38,-93)).close().assemble().finalize().extrude(-35))