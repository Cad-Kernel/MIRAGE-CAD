import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,0))
r=w0.workplane(offset=-73/2).box(164,200,73).union(w0.sketch().circle(59).circle(39,mode='s').finalize().extrude(73))