params = Parameters()
params.add('center_hole_radius', 9.46, min=3.0, max=16.0, semantic_type='inner_radius')
params.add('hole_radius', 2.64, min=0.8, max=5.0, semantic_type='hole_radius')
params.add('thickness', 6.1, min=2.0, max=14.0, semantic_type='thickness')

part = Part('flluma_0093772', category='crescent_lug_profile', parameters=params, seed=20354286, sample_id='flluma_0093772', units='mm')
sketch = part.sketch_polygon(name='crescent_lug_outer_profile', points=[[-38.54, -3.32], [-27.3, -17.73], [1.61, -23.27], [35.33, -14.4], [41.76, 1.11], [30.51, 15.51], [6.42, 22.16], [-17.67, 18.84], [-35.33, 9.97]], closed=True, semantic_type='extrude_profile')
solid = part.extrude(name='extrude_crescent_lug', profile=sketch, height=params['thickness'], semantic_type='extruded_plate')
holes = part.hole_pattern(name='crescent_lug_mounting_holes', target=solid.top_face(), radius=params['hole_radius'], depth='through', positions=[[-24.09, 3.32], [25.7, -2.77]], semantic_type='mounting_hole')
holes_2 = part.hole_pattern(name='crescent_center_hole', target=holes.top_face(), radius=params['center_hole_radius'], depth='through', positions=[[0.0, 0.0]], semantic_type='clearance_hole')

__all__ = ['part']
