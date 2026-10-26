import cadquery as cq
w0=cq.Workplane('YZ',origin=(-100,0,0))
r=w0.sketch().segment((-13,-16),(13,-16)).segment((13,-10)).segment((-6,-10)).segment((-6,16)).segment((-13,16)).segment((-13,1)).segment((-12,1)).segment((-12,0)).segment((-13,0)).close().assemble().push([(-8,5)]).circle(3,mode='s').finalize().extrude(200)