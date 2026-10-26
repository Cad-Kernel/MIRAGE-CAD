params = Parameters()
params.add('hole_radius', 1.23, min=0.8, max=5.0, semantic_type='hole_radius')
params.add('pocket_length', 13.1, min=6.0, max=38.0, semantic_type='pocket_length')
params.add('pocket_width', 10.1, min=4.0, max=26.0, semantic_type='pocket_width')
params.add('thickness', 6.2, min=2.0, max=14.0, semantic_type='thickness')

part = Part('flluma_0005001', category='asymmetric_tab_profile_foot', parameters=params, seed=20265515, sample_id='flluma_0005001', units='mm')
asymmetric_tab_foot = part.asymmetric_tab_profile_foot(name='asymmetric_tab_foot_body', profile='tab_profile_18', thickness=params['thickness'], hole_radius=params['hole_radius'], hole_positions=[[-3.12, -16.8], [3.12, -16.8], [-3.12, 16.8], [3.12, 16.8]], pocket_length=params['pocket_length'], pocket_width=params['pocket_width'], pocket_height=3.0, semantic_type='asymmetric_tab_foot')

__all__ = ['part']