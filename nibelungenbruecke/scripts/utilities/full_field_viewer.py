"""
Full-field temperature viewer for PVD/VTU time-series data.

Renders a mid-z cross-section of the 3D tetrahedral mesh for every timestep
as an animated GIF and displays it inline in a Jupyter notebook.

Usage:
    from nibelungenbruecke.scripts.utilities.full_field_viewer import show_full_field_widget
    show_full_field_widget("/path/to/pv_output.pvd")
"""

import os
import xml.etree.ElementTree as ET

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
from matplotlib.animation import FuncAnimation, PillowWriter
from IPython.display import display, Image
import pyvista as pv


def show_full_field_widget(pvd_file, scalar="temperature", gif_path=None, fps=8):
    """Render a mid-z cross-section animation for a PVD/VTU time series.

    Parses the PVD manifest, extracts a horizontal mid-z slice from each VTU
    timestep, and saves an animated GIF that is then displayed inline.

    Parameters
    ----------
    pvd_file : str
        Path to the PVD collection file that references VTU time steps.
    scalar : str
        Name of the point-data array to visualise (default: ``"temperature"``).
    gif_path : str, optional
        Where to save the animated GIF.  Defaults to a ``figures/`` directory
        next to the PVD file.
    fps : int
        Frames per second for the saved animation (default: 8).
    """
    pvd_file = os.path.abspath(pvd_file)
    pvd_dir  = os.path.dirname(pvd_file)

    # --- Parse PVD manifest ---
    tree = ET.parse(pvd_file)
    pvd_root = tree.getroot()
    entries = [
        (float(ds.attrib["timestep"]),
         os.path.join(pvd_dir, ds.attrib["file"]))
        for ds in pvd_root.findall(".//DataSet")
    ]
    if not entries:
        print("No DataSet entries found in the PVD file - nothing to display.")
        return

    timesteps = [e[0] for e in entries]
    vtu_paths = [e[1] for e in entries]

    print(f"Loading {len(timesteps)} time steps from {pvd_file} ...")

    # --- Load all meshes ---
    meshes = {}
    for t, path in zip(timesteps, vtu_paths):
        mesh = pv.read(path)
        if scalar in mesh.point_data:
            mesh.set_active_scalars(scalar)
        meshes[t] = mesh

    mesh0 = meshes[timesteps[0]]
    pts = mesh0.points
    x, y, z = pts[:, 0], pts[:, 1], pts[:, 2]

    print(f"Done. t_min = {timesteps[0]:.0f} s, t_max = {timesteps[-1]:.0f} s")
    print(f"Mesh: {len(x)} nodes, {mesh0.n_cells} cells")

    # --- Build mid-z cross-section triangulation (topology fixed across steps) ---
    z_mid  = float(z.min() + (z.max() - z.min()) / 2)
    slice0 = mesh0.slice(normal="z", origin=[0, 0, z_mid]).triangulate()
    s_pts  = slice0.points
    xs, ys = s_pts[:, 0], s_pts[:, 1]
    faces  = slice0.faces.reshape(-1, 4)[:, 1:]
    triang = mtri.Triangulation(xs, ys, faces)

    print(f"Slice: {len(xs)} nodes, {len(faces)} triangles  (z = {z_mid:.2f} m)")

    # --- Pre-extract scalar values for every timestep ---
    def _slice_scalar(mesh):
        s = mesh.slice(normal="z", origin=[0, 0, z_mid]).triangulate()
        s.set_active_scalars(scalar)
        return s[scalar]

    slice_vals = {t: _slice_scalar(meshes[t]) for t in timesteps}

    t_all = np.concatenate(list(slice_vals.values()))
    vmin, vmax = float(t_all.min()), float(t_all.max())
    print(f"{scalar} range: {vmin:.2f} - {vmax:.2f}")

    # --- Build and save animated GIF ---
    if gif_path is None:
        fig_dir  = os.path.join(pvd_dir, "figures")
        gif_path = os.path.join(fig_dir, f"{scalar}_animation.gif")
    os.makedirs(os.path.dirname(gif_path), exist_ok=True)

    fig, ax = plt.subplots(figsize=(9, 5))
    tcf = ax.tripcolor(triang, slice_vals[timesteps[0]], shading="gouraud",
                       cmap="RdYlBu_r", vmin=vmin, vmax=vmax)
    fig.colorbar(tcf, ax=ax, label=scalar.capitalize())
    ax.set_aspect("equal")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    title = ax.set_title(
        f"{scalar.capitalize()} (z = {z_mid:.1f} m)  -  "
        f"t = {timesteps[0]:.0f} s  ({timesteps[0]/3600:.2f} h)"
    )
    plt.tight_layout()

    def _update(frame):
        t = timesteps[frame]
        tcf.set_array(slice_vals[t])
        title.set_text(
            f"{scalar.capitalize()} (z = {z_mid:.1f} m)  -  "
            f"t = {t:.0f} s  ({t/3600:.2f} h)"
        )
        return (tcf,)

    ani = FuncAnimation(fig, _update, frames=len(timesteps), interval=120, blit=False)
    ani.save(gif_path, writer=PillowWriter(fps=fps))
    plt.close(fig)

    print(f"Saved: {gif_path}")
    display(Image(gif_path))
