params = Parameters()
params.add('hole_radius', 1.2, min=0.8, max=5.0, semantic_type='hole_radius')
params.add('pocket_length', 17.0, min=6.0, max=40.0, semantic_type='pocket_length')
params.add('pocket_width', 11.93, min=4.0, max=26.0, semantic_type='pocket_width')
params.add('thickness', 7.9, min=3.0, max=16.0, semantic_type='thickness')

part = Part('flluma_0018059', category='stepped_profile_mount', parameters=params, seed=20278573, sample_id='flluma_0018059', units='mm')
sketch = part.sketch_polygon(name='stepped_outer_profile', points=[[-39.0, -13.57], [-9.36, -13.57], [-9.36, -4.79], [14.04, -4.79], [14.04, -13.57], [39.0, -13.57], [39.0, 11.97], [17.16, 11.97], [17.16, 3.19], [-14.04, 3.19], [-14.04, 14.36], [-39.0, 14.36]], closed=True, semantic_type='extrude_profile')
solid = part.extrude(name='extrude_stepped_mount', profile=sketch, height=params['thickness'], semantic_type='extruded_solid')
holes = part.hole_pattern(name='stepped_mount_holes', target=solid.top_face(), radius=params['hole_radius'], depth='through', positions=[[-26.52, -7.98], [26.52, 7.18]], semantic_type='mounting_hole')
pocket = part.rectangular_pocket(name='stepped_mount_recess', target=holes.top_face(), length=params['pocket_length'], width=params['pocket_width'], depth=2.212, semantic_type='pocket')

__all__ = ['part']