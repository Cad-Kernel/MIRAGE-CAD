params = Parameters()
params.add('hole_radius', 1.84, min=0.8, max=5.0, semantic_type='hole_radius')
params.add('pocket_length', 15.46, min=6.0, max=40.0, semantic_type='pocket_length')
params.add('pocket_width', 10.0, min=4.0, max=26.0, semantic_type='pocket_width')
params.add('thickness', 9.3, min=3.0, max=16.0, semantic_type='thickness')

part = Part('flluma_0002814', category='stepped_profile_mount', parameters=params, seed=20263328, sample_id='flluma_0002814', units='mm')
sketch = part.sketch_polygon(name='stepped_outer_profile', points=[[-42.0, -14.28], [-10.08, -14.28], [-10.08, -5.04], [15.12, -5.04], [15.12, -14.28], [42.0, -14.28], [42.0, 12.6], [18.48, 12.6], [18.48, 3.36], [-15.12, 3.36], [-15.12, 15.12], [-42.0, 15.12]], closed=True, semantic_type='extrude_profile')
solid = part.extrude(name='extrude_stepped_mount', profile=sketch, height=params['thickness'], semantic_type='extruded_solid')
holes = part.hole_pattern(name='stepped_mount_holes', target=solid.top_face(), radius=params['hole_radius'], depth='through', positions=[[-28.56, -8.4], [28.56, 7.56]], semantic_type='mounting_hole')
pocket = part.rectangular_pocket(name='stepped_mount_recess', target=holes.top_face(), length=params['pocket_length'], width=params['pocket_width'], depth=2.604, semantic_type='pocket')

__all__ = ['part']