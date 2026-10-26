import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-7))
r=w0.sketch().rect(200,198).rect(176,174,mode='s').finalize().extrude(14)