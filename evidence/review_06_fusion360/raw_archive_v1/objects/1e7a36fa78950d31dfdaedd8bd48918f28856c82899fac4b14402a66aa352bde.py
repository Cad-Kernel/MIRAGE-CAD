import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-67))
r=w0.workplane(offset=-33/2).cylinder(33,25).union(w0.sketch().segment((-45,-45),(45,-45)).segment((45,45)).segment((-45,45)).segment((-45,28)).segment((45,29)).segment((45,43)).segment((41,43)).segment((41,45)).segment((-45,45)).close().assemble().finalize().extrude(167))