params = Parameters()
params.add('height', 10.6, min=12, max=80, semantic_type='overall_height')
params.add('hole_radius', 1.14, min=1, max=8, semantic_type='hole_radius')
params.add('rib_height', 4.1, min=2.0, max=14.0, expression='thickness * 0.89', semantic_type='rib_height')
params.add('rib_step', 18.1, min=3.0, max=24.0, expression='width * 0.14', semantic_type='rib_step')
params.add('rib_width', 2.7, min=1.0, max=5.0, expression='height * 0.258', semantic_type='rib_width')
params.add('thickness', 10, min=3, max=25, semantic_type='thickness')
params.add('width', 32.4, min=20, max=120, semantic_type='overall_width')

part = Part('flluma_0005001', category='linear_ribbed_heat_sink_mount', parameters=params, seed=20265516, sample_id='flluma_0005001', units='mm')
plate = part.plate(name='ribbed_mount_base', width=params['width'], height=params['height'], thickness=params['thickness'], semantic_type='base_plate')
box = part.box(name='heat_sink_rib_seed', length=params['rib_width'], width=params['rib_height'], height=params['rib_step'], semantic_type='rib')
moved = part.translate(name='place_first_heat_sink_rib', target=box, offset=[-15.35, 0.0, 4.05], semantic_type='placement')
linear_pattern = part.linear_pattern(name='linear_heat_sink_rib_array', target=moved.top_face(), count=2, step=[params['rib_step'], 0.0, 0.0], semantic_type='support_rib')
join = part.boolean_join(name='join_heat_sink_ribs', target=plate.top_face(), tool=linear_pattern.top_face(), semantic_type='support_rib')
holes = part.hole_pattern(name='ribbed_mount_corner_holes', target=join.top_face(), radius=params['hole_radius'], depth='through', positions=[[-7.824, 0.0], [8.808, 5.328]], semantic_type='mounting_hole')

__all__ = ['part']