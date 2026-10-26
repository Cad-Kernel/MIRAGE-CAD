params = Parameters()
params.add('hole_radius', 1.43, min=0.8, max=5.0, semantic_type='hole_radius')
params.add('pocket_length', 10.74, min=6.0, max=40.0, semantic_type='pocket_length')
params.add('pocket_width', 14.14, min=4.0, max=26.0, semantic_type='pocket_width')
params.add('thickness', 10.1, min=3.0, max=16.0, semantic_type='thickness')

part = Part('flluma_0005001', category='stepped_profile_mount', parameters=params, seed=20265518, sample_id='flluma_0005001', units='mm')
sketch = part.sketch_polygon(name='stepped_outer_profile', points=[[10.5, 1.15], [-5.1, 1.15], [-5.1, 8.4], [-10.5, 8.4], [-10.5, 1.15]], closed=True, semantic_type='extrude_profile')
solid = part.extrude(name='extrude_stepped_mount', profile=sketch, height=params['thickness'], semantic_type='extruded_plate')
holes = part.hole_pattern(name='stepped_mount_holes', target=solid.top_face(), radius=params['hole_radius'], depth='through', positions=[[-2.66, 2.65], [2.66, -2.65]], semantic_type='mounting_hole')
pocket = part.rectangular_pocket(name='stepped_mount_recess', target=holes.top_face(), length=params['pocket_length'], width=params['pocket_width'], depth=2.42, semantic_type='pocket')

__all__ = ['part']