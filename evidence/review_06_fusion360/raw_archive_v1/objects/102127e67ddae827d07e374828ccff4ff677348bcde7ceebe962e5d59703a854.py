import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,27))
r=w0.sketch().circle(66).circle(51,mode='s').finalize().extrude(-127).union(w0.sketch().segment((-28,-67),(28,-67)).segment((28,-66)).arc((73,0),(28,66)).segment((28,67)).segment((-28,67)).segment((-28,66)).arc((-73,0),(-28,-66)).close().assemble().finalize().extrude(-73)).union(w0.workplane(offset=73/2).cylinder(73,58))