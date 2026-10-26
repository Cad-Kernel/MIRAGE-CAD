params = Parameters()
params.add('height', 11.42, min=4.0, max=28.0, semantic_type='primitive_height')
params.add('radius', 2.0, min=1.0, max=8.0, semantic_type='primitive_radius')

part = Part('flluma_0077803', category='capsule_stock', parameters=params, seed=21338320, sample_id='flluma_0077803', units='mm')
capsule = part.capsule(name='capsule_stock_body', radius=params['radius'], height=params['height'], semantic_type='primitive_stock')

__all__ = ['part']