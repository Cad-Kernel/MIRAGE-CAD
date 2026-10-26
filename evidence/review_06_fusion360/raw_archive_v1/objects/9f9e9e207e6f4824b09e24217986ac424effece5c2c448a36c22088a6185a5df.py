import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,40))
r=w0.sketch().arc((-50,-64),(-37,-89),(-13,-100)).segment((13,-100)).arc((37,-90),(50,-65)).segment((50,65)).arc((37,89),(13,100)).segment((-13,100)).arc((-37,89),(-50,65)).close().assemble().push([(19,0)]).circle(20,mode='s').finalize().extrude(-80)