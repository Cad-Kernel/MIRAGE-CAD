params = Parameters()
params.add('height', 50.1, min=12, max=80, semantic_type='overall_height')
params.add('hole_radius', 1.53, min=1, max=8, semantic_type='hole_radius')
params.add('thickness', 7.7, min=3, max=25, semantic_type='thickness')
params.add('width', 52.1, min=20, max=120, semantic_type='overall_width')

part = Part('flluma_0007100', category='heat_sink_base', parameters=params, seed=20267614, sample_id='flluma_0007100', units='mm')
plate = part.plate(name='thermal_base_plate', width=params['width'], height=params['height'], thickness=params['thickness'], semantic_type='base_plate')
holes = part.hole_pattern(name='corner_mounting_holes', target=plate.top_face(), radius=params['hole_radius'], depth='through', positions=[[-14.588, -12.525], [14.588, -12.525], [-14.588, 12.525], [14.588, 12.525]], semantic_type='mounting_hole')
box = part.box(name='thermal_manager_box', length=params['width'], width=params['height'], height=params['thickness'], semantic_type='thermal_store')
moved = part.translate(name='place_thermal_box', target=box, offset=[0.0, 21.55, 3.85], semantic_type='placement')
join = part.boolean_join(name='join_thermal_box', target=holes, tool=moved, semantic_type='joined_boss')

__all__ = ['part']