params = Parameters()
params.add('hole_radius', 1.23, min=0.8, max=5.0, semantic_type='hole_radius')
params.add('pocket_length', 11.14, min=6.0, max=42.0, semantic_type='pocket_length')
params.add('pocket_width', 10.14, min=4.0, max=26.0, semantic_type='pocket_width')
params.add('thickness', 9.1, min=3.0, max=18.0, semantic_type='thickness')

part = Part('flluma_0005001', category='trapezoid_profile_foot', parameters=params, seed=20265515, sample_id='flluma_0005001', units='mm')
sketch = part.sketch_polygon(name='trapezoid_outer_profile', points=[[-25.65, -23.48], [25.65, -23.48], [16.11, 23.48], [-16.11, 23.48]], closed=True, semantic_type='extrude_profile')
solid = part.extrude(name='extrude_trapezoid_foot', profile=sketch, height=params['thickness'], semantic_type='extruded_solid')
holes = part.hole_pattern(name='trapezoid_foot_holes', target=solid.top_face(), radius=params['hole_radius'], depth='through', positions=[[-12.31, -10.74], [12.31, -10.74]], semantic_type='mounting_hole')
pocket = part.rectangular_pocket(name='trapezoid_top_recess', target=holes.top_face(), length=params['pocket_length'], width=params['pocket_width'], depth=2.275, semantic_type='pocket')

__all__ = ['part']