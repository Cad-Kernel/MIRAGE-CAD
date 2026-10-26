params = Parameters()
params.add('radius_x', 10.1, min=1.0, max=12.0, semantic_type='ellipsoid_radius_x')
params.add('radius_y', 10.1, min=1.0, max=12.0, semantic_type='ellipsoid_radius_y')
params.add('radius_z', 4.1, min=1.0, max=8.0, semantic_type='ellipsoid_radius_z')

part = Part('flluma_0001001', category='ellipsoid_stock', parameters=params, seed=20261516, sample_id='flluma_0001001', units='mm')
ellipsoid = part.ellipsoid(name='ellipsoid_stock_body', radii=[params['radius_x'], params['radius_y'], params['radius_z']], semantic_type='primitive_stock')

__all__ = ['part']