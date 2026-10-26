import cadquery as cq
w0=cq.Workplane('YZ',origin=(7,0,0))
r=w0.sketch().segment((-100,-73),(100,-73)).segment((67,73)).segment((-87,73)).close().assemble().finalize().extrude(-13)