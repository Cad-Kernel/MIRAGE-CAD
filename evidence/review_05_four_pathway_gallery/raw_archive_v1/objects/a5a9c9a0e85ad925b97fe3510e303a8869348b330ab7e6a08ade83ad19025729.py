params = Parameters()
params.add('height', 37.2, min=12, max=80, semantic_type='overall_height')
params.add('hole_radius', 2.04, min=1, max=8, semantic_type='hole_radius')
params.add('rib_height', 7.72, min=2.0, max=18.0, expression='thickness * 0.965', semantic_type='rib_height')
params.add('rib_length', 53.5, min=12.0, max=100.0, expression='width * 0.721', semantic_type='rib_length')
params.add('rib_offset_y', 5.25, min=2.0, max=24.0, expression='height * 0.141', semantic_type='rib_offset')
params.add('rib_width', 3.27, min=2.0, max=12.0, expression='max(2.0, height * 0.088)', semantic_type='rib_width')
params.add('thickness', 8, min=3, max=25, semantic_type='thickness')
params.add('width', 74.2, min=20, max=120, semantic_type='overall_width')

part = Part('flluma_0095386', category='ribbed_support_plate', parameters=params, seed=20355900, sample_id='flluma_0095386', units='mm')
ribbed_plate = part.ribbed_support_plate(name='ribbed_support_plate_body', width=params['width'], height=params['height'], thickness=params['thickness'], hole_radius=params['hole_radius'], hole_positions=[[-20.776, -9.3], [20.776, -9.3], [-20.776, 9.3], [20.776, 9.3]], rib_length=params['rib_length'], rib_width=params['rib_width'], rib_height=params['rib_height'], rib_offset_y=params['rib_offset_y'], semantic_type='ribbed_support_plate')

__all__ = ['part']
