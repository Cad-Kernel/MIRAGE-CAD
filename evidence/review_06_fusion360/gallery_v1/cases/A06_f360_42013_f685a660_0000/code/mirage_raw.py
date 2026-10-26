params = Parameters()
params.add('radius_x', 10.18, min=4.0, max=12.0, semantic_type='radius_x')
params.add('radius_y', 10.18, min=4.0, max=12.0, semantic_type='radius_y')
params.add('radius_z', 10.18, min=4.0, max=12.0, semantic_type='radius_z')

part = Part('flluma_0005001', category='ellipsoid_stock', parameters=params, seed=20265516, sample_id='flluma_0005001', units='mm')
ellipsoid = part.ellipsoid(name='ellipsoid_stock_body', radii=[params['radius_x'], params['radius_y'], params['radius_z']], semantic_type='primitive_stock')

__all__ = ['part']