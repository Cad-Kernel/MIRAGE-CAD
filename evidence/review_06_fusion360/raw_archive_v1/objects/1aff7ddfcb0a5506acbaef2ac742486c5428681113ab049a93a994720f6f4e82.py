import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-58,0))
w1=cq.Workplane('ZX',origin=(0,-47,0))
r=w0.workplane(offset=158/2).cylinder(158,13).union(w1.sketch().circle(33).circle(17,mode='s').finalize().extrude(-53))