import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,2,0))
r=w0.sketch().segment((-17,-47),(8,-100)).segment((17,-96)).segment((17,-53)).arc((11,-56),(5,-57)).segment((5,-58)).segment((1,-58)).segment((1,-57)).arc((-2,-56),(-8,-55)).segment((17,43)).segment((17,94)).arc((-14,61),(-4,17)).arc((-11,-7),(-13,-31)).arc((-17,-39),(-17,-47)).assemble().finalize().extrude(-4)