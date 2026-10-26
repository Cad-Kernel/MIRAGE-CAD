params = Parameters()
params.add('radius', 5.03, min=1.5, max=16.0, semantic_type='sphere_radius')

part = Part('flluma_0065849', category='sphere_stock', parameters=params, seed=20326363, sample_id='flluma_0065849', units='mm')
sphere = part.sphere(name='sphere_stock_body', radius=params['radius'], semantic_type='primitive_stock')

__all__ = ['part']