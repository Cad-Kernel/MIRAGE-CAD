params = Parameters()
params.add('radius', 1.18, min=0.8, max=6.0, semantic_type='sphere_radius')

part = Part('flluma_0005000', category='sphere_stock', parameters=params, seed=20265514, sample_id='flluma_0005000', units='mm')
sphere = part.sphere(name='sphere_stock_body', radius=params['radius'], semantic_type='primitive_stock')

__all__ = ['part']