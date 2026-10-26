params = Parameters()
params.add('radius_x', 7.05, min=1.0, max=12.0, semantic_type='ellipsoid_radius_x')
params.add('radius_y', 2.49, min=1.0, max=12.0, semantic_type='ellipsoid_radius_y')
params.add('radius_z', 2.94, min=1.0, max=12.0, semantic_type='ellipsoid_radius_z')

part = Part('flluma_0065632', category='ellipsoid_stock', parameters=params, seed=20326146, sample_id='flluma_0065632', units='mm')
ellipsoid = part.ellipsoid(name='ellipsoid_stock_body', radii=[params['radius_x'], params['radius_y'], params['radius_z']], semantic_type='primitive_stock')

__all__ = ['part']