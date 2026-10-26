params = Parameters()
params.add('height', 8.67, min=4.0, max=28.0, semantic_type='primitive_height')
params.add('radius', 2.23, min=1.0, max=8.0, semantic_type='primitive_radius')

part = Part('flluma_0068255', category='capsule_stock', parameters=params, seed=22328775, sample_id='flluma_0068255', units='mm')
capsule = part.capsule(name='capsule_stock_body', radius=params['radius'], height=params['height'], semantic_type='primitive_stock')

__all__ = ['part']