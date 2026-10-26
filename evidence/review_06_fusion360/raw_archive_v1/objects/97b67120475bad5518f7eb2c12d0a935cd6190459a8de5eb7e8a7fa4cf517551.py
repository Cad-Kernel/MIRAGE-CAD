import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,25,0))
r=w0.sketch().arc((-17,-100),(3,-76),(16,-47)).segment((16,-36)).segment((16,-35)).segment((17,-35)).segment((17,100)).segment((0,100)).segment((0,14)).arc((-8,3),(-17,0)).close().assemble().finalize().extrude(-50)