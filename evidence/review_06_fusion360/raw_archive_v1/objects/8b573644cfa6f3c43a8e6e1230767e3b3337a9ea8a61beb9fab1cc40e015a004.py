import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,91,0))
w1=cq.Workplane('ZX',origin=(0,-97,0))
r=w0.sketch().segment((-19,-42),(2,-42)).segment((2,42)).segment((-5,42)).segment((-5,52)).segment((-7,52)).segment((-7,42)).segment((-19,42)).segment((-19,32)).segment((-17,32)).segment((-17,-40)).segment((-19,-40)).close().assemble().push([(-17,27)]).circle(1,mode='s').push([(-16.5,-19.5)]).rect(1,3,mode='s').push([(-15.5,27)]).rect(1,2,mode='s').finalize().extrude(-188).union(w0.workplane(offset=9/2).box(76,118,9)).union(w1.workplane(offset=-3/2).moveTo(-19,0).box(38,104,3))