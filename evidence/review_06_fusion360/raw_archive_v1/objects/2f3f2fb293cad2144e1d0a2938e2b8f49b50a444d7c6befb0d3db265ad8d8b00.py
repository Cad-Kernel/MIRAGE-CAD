import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-87,0))
r=w0.workplane(offset=-13/2).box(82,82,13).union(w0.sketch().circle(39).circle(29,mode='s').finalize().extrude(187))