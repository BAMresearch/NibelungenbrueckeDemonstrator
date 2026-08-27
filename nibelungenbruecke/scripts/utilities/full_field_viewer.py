"""
Full-field viewer for PVD/VTU time-series data.

Renders the full-field response of the simulation for every timestep as an
animated GIF and displays it inline in a Jupyter notebook.

Two views are available:

``"3d"``
    The exterior surface of the tetrahedral mesh, coloured by the scalar
    field.  This is the default for volumetric (3D) meshes.
``"slice"``
    A cross-section of the mesh at mid-z.  This is the default for planar
    (2D) meshes, where a 3D view carries no additional information.

The animation is built with matplotlib only, so it does not require an
OpenGL context and works on headless machines (Binder, JupyterHub, CI).

Usage:
    from nibelungenbruecke.scripts.utilities.full_field_viewer import show_full_field_widget
    show_full_field_widget("/path/to/pv_output.pvd")
"""

import os
import xml.etree.ElementTree as ET

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
from matplotlib.animation import FuncAnimation, PillowWriter
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from IPython.display import display, Image
import pyvista as pv


def _read_pvd(pvd_file):
    """Return the ``(timesteps, vtu_paths)`` listed in a PVD manifest."""
    pvd_dir = os.path.dirname(pvd_file)
    root = ET.parse(pvd_file).getroot()
    entries = [
        (float(ds.attrib["timestep"]), os.path.join(pvd_dir, ds.attrib["file"]))
        for ds in root.findall(".//DataSet")
    ]
    return [e[0] for e in entries], [e[1] for e in entries]


def _celsius_offset(values, scalar, celsius):
    """Return the offset to subtract to display *values* in degrees Celsius."""
    if celsius == "auto":
        celsius = scalar == "temperature" and float(np.median(values)) > 200.0
    return (273.15, "[°C]") if celsius else (0.0, "")


def show_full_field_widget(pvd_file, scalar="temperature", gif_path=None, fps=8,
                           view="auto", max_frames=None, celsius="auto"):
    """Render an animation of the full-field response of a PVD/VTU time series.

    Parses the PVD manifest, builds one frame per time step and saves an
    animated GIF that is then displayed inline.

    Parameters
    ----------
    pvd_file : str
        Path to the PVD collection file that references the VTU time steps.
    scalar : str
        Name of the point-data array to visualise (default: ``"temperature"``).
    gif_path : str, optional
        Where to save the animated GIF.  Defaults to a ``figures/`` directory
        next to the PVD file.
    fps : int
        Frames per second for the saved animation (default: 8).
    view : {"auto", "3d", "slice"}
        ``"3d"`` renders the exterior surface of the mesh, ``"slice"`` a
        cross-section at mid-z.  ``"auto"`` picks ``"slice"`` for planar
        meshes and ``"3d"`` otherwise.
    max_frames : int, optional
        Render at most this many time steps, sampled evenly over the series.
        Useful to keep the GIF small for long simulations.
    celsius : bool or "auto"
        Convert the values from kelvin to degrees Celsius.  ``"auto"``
        converts when *scalar* is ``"temperature"`` and the values are
        clearly in kelvin.
    """
    pvd_file = os.path.abspath(pvd_file)
    timesteps, vtu_paths = _read_pvd(pvd_file)
    if not timesteps:
        print("No DataSet entries found in the PVD file - nothing to display.")
        return

    if max_frames is not None and max_frames < len(timesteps):
        idx = np.linspace(0, len(timesteps) - 1, max_frames).round().astype(int)
        timesteps = [timesteps[i] for i in idx]
        vtu_paths = [vtu_paths[i] for i in idx]

    print(f"Loading {len(timesteps)} time steps from {pvd_file} ...")
    meshes = []
    for path in vtu_paths:
        mesh = pv.read(path)
        if scalar in mesh.point_data:
            mesh.set_active_scalars(scalar)
        meshes.append(mesh)

    mesh0 = meshes[0]
    z = mesh0.points[:, 2]
    if view == "auto":
        extents = mesh0.points.ptp(axis=0)
        view = "slice" if float(extents.min()) < 1e-9 else "3d"

    print(f"Done. t_min = {timesteps[0]:.0f} s, t_max = {timesteps[-1]:.0f} s")
    print(f"Mesh: {mesh0.n_points} nodes, {mesh0.n_cells} cells  (view: {view})")

    if gif_path is None:
        gif_path = os.path.join(os.path.dirname(pvd_file), "figures",
                                f"{scalar}_animation_{view}.gif")
    os.makedirs(os.path.dirname(gif_path), exist_ok=True)

    if view == "3d":
        fig, update = _build_surface_animation(meshes, timesteps, scalar, celsius)
    else:
        fig, update = _build_slice_animation(meshes, timesteps, scalar, celsius, z)

    ani = FuncAnimation(fig, update, frames=len(timesteps), interval=120, blit=False)
    ani.save(gif_path, writer=PillowWriter(fps=fps))
    plt.close(fig)

    print(f"Saved: {gif_path}")
    display(Image(gif_path))
    return gif_path


def _build_surface_animation(meshes, timesteps, scalar, celsius):
    """Build the 3D exterior-surface animation, returning ``(figure, update)``."""
    # Surface extraction is a plain VTK filter: it needs no OpenGL context.
    surf0 = meshes[0].extract_surface().triangulate()
    pts = surf0.points
    tris = surf0.faces.reshape(-1, 4)[:, 1:]
    values = np.array([
        np.asarray(m.extract_surface().point_data[scalar]) for m in meshes
    ])

    offset, unit = _celsius_offset(values, scalar, celsius)
    values = values - offset
    vmin, vmax = float(values.min()), float(values.max())
    print(f"{scalar} range: {vmin:.2f} - {vmax:.2f} {unit}".rstrip())

    cmap = plt.get_cmap("RdYlBu_r")
    norm = Normalize(vmin, vmax)
    face_values = values[:, tris].mean(axis=2)

    x, y, z = pts[:, 0], pts[:, 1], pts[:, 2]
    # Draw with the bridge axis (z) horizontal, so the deck spans the frame.
    verts = pts[tris][:, :, [2, 0, 1]]

    fig = plt.figure(figsize=(9.5, 3.0))
    # The axes box is deliberately taller than the figure: the mesh is very
    # elongated and occupies only a horizontal band of the 3D box, so the
    # unused top and bottom of that box fall outside the figure.
    ax = fig.add_axes([-0.02, -0.40, 0.88, 1.80], projection="3d")
    collection = Poly3DCollection(verts, linewidths=0)
    ax.add_collection3d(collection)
    ax.set_xlim(z.min(), z.max())
    ax.set_ylim(x.min(), x.max())
    ax.set_zlim(y.min(), y.max())
    ax.set_box_aspect((np.ptp(z), np.ptp(x), np.ptp(y)))
    ax.view_init(elev=24, azim=-62)
    ax.set_axis_off()

    cax = fig.add_axes([0.88, 0.18, 0.018, 0.64])
    fig.colorbar(ScalarMappable(norm=norm, cmap=cmap), cax=cax,
                 label=f"{scalar.capitalize()} {unit}".strip())
    title = fig.text(0.43, 0.95, "", ha="center", va="top", fontsize=11)

    def _update(frame):
        collection.set_facecolor(cmap(norm(face_values[frame])))
        t = timesteps[frame]
        title.set_text(f"{scalar.capitalize()} - t = {t:.0f} s ({t / 3600:.1f} h)")
        return (collection,)

    _update(0)
    return fig, _update


def _build_slice_animation(meshes, timesteps, scalar, celsius, z):
    """Build the mid-z cross-section animation, returning ``(figure, update)``."""
    z_mid = float(z.min() + (z.max() - z.min()) / 2)
    slice0 = meshes[0].slice(normal="z", origin=[0, 0, z_mid]).triangulate()
    s_pts = slice0.points
    xs, ys = s_pts[:, 0], s_pts[:, 1]
    faces = slice0.faces.reshape(-1, 4)[:, 1:]
    triang = mtri.Triangulation(xs, ys, faces)

    print(f"Slice: {len(xs)} nodes, {len(faces)} triangles  (z = {z_mid:.2f} m)")

    def _slice_scalar(mesh):
        s = mesh.slice(normal="z", origin=[0, 0, z_mid]).triangulate()
        s.set_active_scalars(scalar)
        return s[scalar]

    values = np.array([_slice_scalar(m) for m in meshes])
    offset, unit = _celsius_offset(values, scalar, celsius)
    values = values - offset
    vmin, vmax = float(values.min()), float(values.max())
    print(f"{scalar} range: {vmin:.2f} - {vmax:.2f} {unit}".rstrip())

    fig, ax = plt.subplots(figsize=(9, 5))
    tcf = ax.tripcolor(triang, values[0], shading="gouraud",
                       cmap="RdYlBu_r", vmin=vmin, vmax=vmax)
    fig.colorbar(tcf, ax=ax, label=f"{scalar.capitalize()} {unit}".strip())
    ax.set_aspect("equal")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    title = ax.set_title("")
    plt.tight_layout()

    def _update(frame):
        tcf.set_array(values[frame])
        t = timesteps[frame]
        title.set_text(
            f"{scalar.capitalize()} (z = {z_mid:.1f} m)  -  "
            f"t = {t:.0f} s  ({t / 3600:.2f} h)"
        )
        return (tcf,)

    _update(0)
    return fig, _update
