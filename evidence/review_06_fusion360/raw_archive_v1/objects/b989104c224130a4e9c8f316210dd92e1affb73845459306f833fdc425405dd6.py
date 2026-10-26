import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,95))
r=w0.sketch().push([(-90,0)]).circle(10).push([(90,0)]).circle(10).finalize().extrude(-190)