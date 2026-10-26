import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,29))
r=w0.sketch().circle(75).circle(57,mode='s').finalize().extrude(-129).union(w0.workplane(offset=42/2).cylinder(42,86)).union(w0.workplane(offset=71/2).cylinder(71,29))