import cadquery as cq
w0=cq.Workplane('YZ',origin=(100,0,0))
r=w0.sketch().arc((-5,-30),(5,0),(-5,30)).close().assemble().finalize().extrude(-200)