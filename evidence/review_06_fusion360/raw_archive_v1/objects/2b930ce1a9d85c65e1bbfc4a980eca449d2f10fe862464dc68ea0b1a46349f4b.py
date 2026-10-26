import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-76,0))
r=w0.workplane(offset=-24/2).cylinder(24,63).union(w0.workplane(offset=149/2).cylinder(149,45)).union(w0.sketch().circle(36).circle(27,mode='s').finalize().extrude(176))