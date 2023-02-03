Here the functions for modelling and meshing the geometry are contained.
- `create_cross_section.py` generates the simplified "box" cross-section for the Nibelungenbrücke. It includes two functions: `create_cross_section2D`, which is currently not soported, and `create_cross_section3D`, which generates 2D surface models of the cross-section at the pilots and at the middle of the span.
- `create_geometry.py` generates the 3D volume geometry from a 2D cross-section. An interpolation between the middle span and the pilots is applied to ressemble the actual geometry of the Nibelungenbrücke.
- `create_mesh.py` meshes the 3D volume geometry of the bridge. Currently only simple mesh refinement options are available.

*INSERT PICTURES HERE?*