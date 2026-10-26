import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,12,0))
r=w0.sketch().segment((-100,-14),(50,-14)).segment((50,-15)).segment((100,-7)).segment((100,15)).segment((88,15)).arc((75,5),(62,15)).segment((-50,14)).segment((-50,8)).arc((-70,-2),(-84,13)).segment((-100,13)).close().assemble().finalize().extrude(-24)