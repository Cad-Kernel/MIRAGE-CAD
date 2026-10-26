import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,25))
r=w0.sketch().segment((-100,-7),(96,-7)).segment((100,-6)).segment((74,7)).segment((-100,7)).close().assemble().finalize().extrude(-50)