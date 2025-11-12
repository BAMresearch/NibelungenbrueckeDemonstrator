import numpy as np
from mpi4py import MPI
from dolfinx.io import gmshio
from dolfinx.geometry import BoundingBoxTree, compute_collisions, compute_closest_entity, create_midpoint_tree


from scipy.spatial import Delaunay

def is_point_inside_cell(cell_geometry: np.ndarray, point: np.ndarray) -> bool:
    """
    Check if a point is inside a 2D or 3D convex cell by triangulation.

    Supports:
        - 2D: triangle (3 points), quadrilateral (4 points)
        - 3D: tetrahedron (4 points), hexahedron (8 points)

    Args:
        cell_geometry (np.ndarray): Shape (n_vertices, dim)
        point (np.ndarray): Shape (dim,)

    Returns:
        bool: True if point is inside the convex cell, False otherwise
    """
    point = np.asarray(point, dtype=np.float64)
    cell_geometry = np.asarray(cell_geometry, dtype=np.float64)

    if cell_geometry.ndim != 2 or point.ndim != 1:
        raise ValueError("Invalid input shape.")

    num_vertices, dim = cell_geometry.shape
    if point.shape[0] != dim:
        raise ValueError(f"Point must be {dim}D, got {point.shape[0]}D.")

    # Use Delaunay triangulation to check if point is inside the convex hull of the cell
    try:
        if (cell_geometry[:, 2:] == 0).all():
            hull = Delaunay(cell_geometry[:, :2])
            inside = hull.find_simplex(point[:2]) >= 0
        else:
            hull = Delaunay(cell_geometry)
            inside = hull.find_simplex(point) >= 0
        return inside
    except Exception as e:
        raise ValueError(f"Unsupported geometry or degenerate cell: {e}")

def is_point_inside_mesh(point, mesh):
    """
    Check if a point is inside the mesh and return the containing cell index.

    Args:
        point (array-like): The coordinates of the point to check.
        mesh (dolfinx.mesh.Mesh): The mesh object.

    Returns:
        (bool, int): A tuple where the first element indicates if the point is inside,
                     and the second element is the cell index if inside, or -1 otherwise.
    """
    # Create a bounding box tree for the mesh
    tree = BoundingBoxTree(mesh, mesh.topology.dim)

    # Use compute_collisions to find candidate cells
    points = np.array([point], dtype=np.float64)
    colliding_cells = compute_collisions(tree, points)

    for cell_index in colliding_cells.links(0):
        # Get the coordinates of the cell's vertices
        cell_geometry = mesh.geometry.x[mesh.topology.connectivity(mesh.topology.dim, 0).links(cell_index)]
        if is_point_inside_cell(cell_geometry, point):
            return True, cell_index

    return False, -1

def project_point_onto_mesh(point, mesh):
    """
    Project a point onto the closest point on the mesh (not limited to nodes).

    Args:
        point (array-like): Coordinates of the point [x, y, z].
        mesh (dolfinx.mesh.Mesh): The mesh object.

    Returns:
        np.ndarray: Coordinates of the closest point on the mesh.
    """
    # Create bounding box trees for facets and midpoints
    facet_tree = BoundingBoxTree(mesh, mesh.topology.dim - 1)
    midpoint_tree = create_midpoint_tree(
        mesh, mesh.topology.dim - 1,
        np.arange(mesh.topology.index_map(mesh.topology.dim - 1).size_local, dtype=np.int32)
    )

    # Compute the closest entity to the point
    points = np.array([point], dtype=np.float64)
    closest_entity_index = compute_closest_entity(facet_tree, midpoint_tree, mesh, points)[0]

    if closest_entity_index == -1:
        raise RuntimeError("Failed to find the closest entity to the point.")

    # Retrieve the vertices of the closest facet
    facet_connectivity = mesh.topology.connectivity(mesh.topology.dim - 1, 0)
    facet_vertices = mesh.geometry.x[facet_connectivity.links(closest_entity_index)]

    # Compute the projection using a centroid approximation
    centroid = np.mean(facet_vertices, axis=0)
    return centroid


def query_point(point, mesh):
    """
    Query if a point is inside the mesh, and if not, project it onto the closest point.

    Args:
        point (array-like): Coordinates of the point [x, y, z].
        mesh (dolfinx.mesh.Mesh): The mesh object.

    Returns:
        (np.ndarray, bool): Closest point on the mesh and whether the point is inside the mesh.
    """
    #path = '../../../use_cases/nibelungenbruecke_demonstrator_self_weight_fenicsxconcrete/input/models/mesh.msh'
    #mesh, cell_tags, facet_tags = gmshio.read_from_msh(path, MPI.COMM_WORLD, 0)
    
    inside, cell_index = is_point_inside_mesh(point, mesh)
    if inside:
        return np.array(point), True

    closest_point = project_point_onto_mesh(point, mesh)
    return closest_point, False


if __name__ == "__main__":

    # Test point
    point = [0.83539223, -0.06666667, 0.36112456]
    result_point, is_inside = query_point(point)
    print(f"Point {point} is inside the mesh: {is_inside}")
    print(f"Closest point on the mesh: {result_point}")
    
    point = [0.5, -0.1, 0.5]
    result_point, is_inside = query_point(point)
    print(f"Point {point} is inside the mesh: {is_inside}")
    print(f"Closest point on the mesh: {result_point}")
    
    
    point = [110.5, -10.1, 10.5]
    result_point, is_inside = query_point(point)
    print(f"Point {point} is inside the mesh: {is_inside}")
    print(f"Closest point on the mesh: {result_point}")


    point = [80, 0.0, 0.0]
    result_point, is_inside = query_point(point)
    print(f"Point {point} is inside the mesh: {is_inside}")
    print(f"Closest point on the mesh: {result_point}")