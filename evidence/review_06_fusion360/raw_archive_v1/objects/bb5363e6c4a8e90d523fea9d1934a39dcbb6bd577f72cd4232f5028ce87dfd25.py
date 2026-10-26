import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-100,0))
w1=cq.Workplane('ZX',origin=(0,-93,0))
r=w0.sketch().segment((-29,-29),(29,-29)).segment((29,29)).segment((-29,29)).segment((-29,22)).segment((-22,22)).segment((-22,26)).segment((-26,26)).segment((-26,22)).segment((-29,22)).close().assemble().finalize().extrude(12).union(w0.sketch().push([(-24,24)]).circle(3).push([(24,-24)]).circle(3).push([(24,24)]).rect(4,4).finalize().extrude(200)).union(w1.workplane(offset=43/2).box(30,38,43))