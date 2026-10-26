import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-17,0))
r=w0.workplane(offset=8/2).cylinder(8,100).union(w0.sketch().circle(100).circle(96,mode='s').circle(38).finalize().extrude(25)).union(w0.sketch().circle(43).circle(38,mode='s').finalize().extrude(34))