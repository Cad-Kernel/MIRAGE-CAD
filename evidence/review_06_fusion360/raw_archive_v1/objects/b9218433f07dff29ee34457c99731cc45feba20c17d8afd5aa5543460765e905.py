import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-30))
r=w0.sketch().segment((-73,-30),(73,-30)).segment((73,-30)).arc((100,0),(73,30)).segment((-73,30)).segment((-73,29)).arc((-100,0),(-73,-30)).assemble().finalize().extrude(-20).union(w0.sketch().push([(-41,-1)]).circle(20).push([(40,-1)]).circle(20).finalize().extrude(80))