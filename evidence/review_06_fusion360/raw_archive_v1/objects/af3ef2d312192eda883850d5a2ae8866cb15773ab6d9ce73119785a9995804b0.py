import cadquery as cq
w0=cq.Workplane('YZ',origin=(100,0,0))
r=w0.sketch().segment((-50,-50),(50,-50)).segment((50,-30)).segment((-10,-10)).segment((-10,10)).segment((50,30)).segment((50,50)).segment((-50,50)).close().assemble().finalize().extrude(-200)