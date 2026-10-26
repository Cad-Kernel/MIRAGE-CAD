params = Parameters()
params.add('clamp_jaw_height', 17.05, min=5.0, max=28.0, expression='thickness * 1.55', semantic_type='clamp_jaw_height')
params.add('clamp_jaw_width', 16.8, min=6.0, max=28.0, expression='width * 0.279', semantic_type='clamp_jaw_width')
params.add('height', 61.7, min=12, max=80, semantic_type='overall_height')
params.add('hole_radius', 2.9, min=1, max=8, semantic_type='hole_radius')
params.add('pocket_width', 23.08, min=8.0, max=40.0, expression='height * 0.374', semantic_type='pocket_width')
params.add('thickness', 11, min=3, max=25, semantic_type='thickness')
params.add('width', 60.2, min=20, max=120, semantic_type='overall_width')

part = Part('flluma_0091123', category='pipe_clamp', parameters=params, seed=20351637, sample_id='flluma_0091123', units='mm')
plate = part.plate(name='clamp_base', width=params['width'], height=params['height'], thickness=params['thickness'], semantic_type='base_plate')
pocket = part.rectangular_pocket(name='pipe_clearance_channel', target=plate.top_face(), length=37.324, width=params['pocket_width'], depth=2.75, semantic_type='pocket')
holes = part.hole_pattern(name='clamp_bolt_holes', target=pocket.top_face(), radius=params['hole_radius'], depth='through', positions=[[-13.244, 0.0], [14.448, 7.404]], semantic_type='bolt_hole_pattern')
box = part.box(name='clamp_jaw_seed', length=params['clamp_jaw_width'], width=params['height'], height=params['clamp_jaw_height'], semantic_type='clamp_jaw')
moved = part.translate(name='place_clamp_jaw', target=box, offset=[21.7, 0.0, 13.825], semantic_type='placement')
mirror = part.mirror(name='mirror_clamp_jaw', target=moved, axis='X', plane=None, semantic_type='pattern')
join = part.boolean_join(name='join_clamp_jaws', target=holes, tool=mirror, semantic_type='mirrored_clamp_jaw')

__all__ = ['part']
