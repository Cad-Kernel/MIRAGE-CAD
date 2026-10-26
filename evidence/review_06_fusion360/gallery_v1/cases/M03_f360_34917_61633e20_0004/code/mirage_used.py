params = Parameters()
params.add('height', 10.73, min=4.0, max=28.0, semantic_type='primitive_height')
params.add('radius', 5.1, min=1.0, max=12.0, semantic_type='primitive_radius')

part = Part('flluma_0005001', category='capsule_stock', parameters=params, seed=20265516, sample_id='flluma_0005001', units='mm')
capsule = part.capsule(name='capsule_stock_body', radius=params['radius'], height=params['height'], semantic_type='primitive_stock')

__all__ = ['part']