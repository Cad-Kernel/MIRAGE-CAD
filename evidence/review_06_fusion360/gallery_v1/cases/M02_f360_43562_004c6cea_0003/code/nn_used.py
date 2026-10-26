params = Parameters()
params.add('hole_radius', 1.51, min=0.8, max=5.0, semantic_type='hole_radius')
params.add('pocket_length', 18.38, min=6.0, max=40.0, semantic_type='pocket_length')
params.add('pocket_width', 6.75, min=4.0, max=26.0, semantic_type='pocket_width')
params.add('thickness', 5.0, min=3.0, max=16.0, semantic_type='thickness')

part = Part('flluma_0041815', category='stepped_profile_mount', parameters=params, seed=20302329, sample_id='flluma_0041815', units='mm')
sketch = part.sketch_polygon(name='stepped_outer_profile', points=[[-35.9, -12.14], [-8.62, -12.14], [-8.62, -4.28], [12.92, -4.28], [12.92, -12.14], [35.9, -12.14], [35.9, 10.71], [15.8, 10.71], [15.8, 2.86], [-12.92, 2.86], [-12.92, 12.85], [-35.9, 12.85]], closed=True, semantic_type='extrude_profile')
solid = part.extrude(name='extrude_stepped_mount', profile=sketch, height=params['thickness'], semantic_type='extruded_solid')
holes = part.hole_pattern(name='stepped_mount_holes', target=solid.top_face(), radius=params['hole_radius'], depth='through', positions=[[-24.41, -7.14], [24.41, 6.43]], semantic_type='mounting_hole')
pocket = part.rectangular_pocket(name='stepped_mount_recess', target=holes.top_face(), length=params['pocket_length'], width=params['pocket_width'], depth=1.4, semantic_type='pocket')

__all__ = ['part']