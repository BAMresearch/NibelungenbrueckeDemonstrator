"""
Convert FEniCS/FEniCSx XDMF+H5 time-series output to a PVD collection of VTU files.

VTK.js (used by jupyterview) requires base64-encoded XML VTU files, NOT raw binary.
Use --encoding base64  (default) for jupyterview / browser viewers.
Use --encoding raw     for ParaView desktop (smaller files).

Usage (from the code/ directory):
    python xdmf_to_vtu_converter.py                          # all steps, base64
    python xdmf_to_vtu_converter.py --max-steps 50           # first 50 steps
    python xdmf_to_vtu_converter.py --encoding raw           # raw binary (ParaView desktop)
    python xdmf_to_vtu_converter.py --out-dir . --pvd pv.pvd # output next to the notebook

Programmatic usage:
    from xdmf_to_vtu_converter import convert_xdmf_to_pvd
    pvd_path = convert_xdmf_to_pvd(h5_file, out_dir, pvd_file)
"""

import os
import h5py
import numpy as np
import meshio


def convert_xdmf_to_pvd(h5_file, out_dir, pvd_file, max_steps=None, encoding="base64"):
    """Convert a FEniCSx XDMF/H5 time-series to a PVD collection of VTU files.

    Parameters
    ----------
    h5_file : str
        Path to the HDF5 file produced by FEniCSx (companion to the .xdmf).
    out_dir : str
        Directory where individual VTU files will be written (created if absent).
    pvd_file : str
        Path for the output .pvd collection file.
    max_steps : int or None
        Limit export to the first *max_steps* time steps.  ``None`` exports all.
    encoding : {"base64", "raw"}
        VTU data encoding.  Use ``"base64"`` for browser/VTK.js viewers and
        ``"raw"`` for ParaView desktop (smaller files).

    Returns
    -------
    str
        Absolute path to the written PVD file.
    """
    os.makedirs(out_dir, exist_ok=True)

    with h5py.File(h5_file, "r") as f:
        raw_points = f["Mesh/mesh/geometry"][:]
        cells_conn = f["Mesh/mesh/topology"][:]

        # Promote 2-D mesh coordinates to 3-D by appending a z=0 column when needed
        if raw_points.shape[1] == 2:
            points = np.column_stack([raw_points, np.zeros(len(raw_points))])
        else:
            points = raw_points

        # Auto-detect cell type from topology column count
        nodes_per_cell = cells_conn.shape[1]
        _cell_type_map = {2: "line", 3: "triangle", 4: "tetra",
                          8: "hexahedron", 6: "wedge", 5: "pyramid"}
        cell_type = _cell_type_map.get(nodes_per_cell, "triangle")

        ts_group  = f["Function/temperature"]
        timesteps = sorted(ts_group.keys(), key=lambda k: int(k))

        if max_steps is not None:
            timesteps = timesteps[:max_steps]

        print(f"Exporting {len(timesteps)} time steps  (encoding={encoding})")

        pvd_entries = []

        for idx, ts_key in enumerate(timesteps):
            t_value     = int(ts_key)
            temperature = ts_group[ts_key][:].flatten()

            mesh = meshio.Mesh(
                points=points,
                cells=[(cell_type, cells_conn)],
                point_data={"temperature": temperature},
            )

            vtu_name = f"pv_output_{idx:05d}.vtu"
            vtu_path = os.path.join(out_dir, vtu_name)
            # base64: binary=True, compression=None  → XML with base64 data (VTK.js compatible)
            # raw:    binary=True, compression default → smaller files for ParaView desktop
            if encoding == "base64":
                mesh.write(vtu_path, file_format="vtu", binary=True, compression=None)
            else:
                mesh.write(vtu_path, file_format="vtu", binary=True)

            pvd_entries.append((t_value, vtu_name))

            if idx % 100 == 0:
                print(f"  step {idx}/{len(timesteps)}  t={t_value}")

    # Write PVD manifest with paths relative to the pvd_file location
    pvd_rel_dir = os.path.relpath(out_dir, os.path.dirname(os.path.abspath(pvd_file)))

    with open(pvd_file, "w") as pvd:
        pvd.write('<?xml version="1.0"?>\n')
        pvd.write('<VTKFile type="Collection" version="0.1" byte_order="LittleEndian">\n')
        pvd.write('  <Collection>\n')
        for t_value, vtu_name in pvd_entries:
            rel_path = os.path.join(pvd_rel_dir, vtu_name).replace("\\", "/")
            pvd.write(f'    <DataSet timestep="{t_value}" group="" part="0" file="{rel_path}"/>\n')
        pvd.write('  </Collection>\n')
        pvd.write('</VTKFile>\n')

    abs_pvd = os.path.abspath(pvd_file)
    print(f"\nDone. PVD written to: {abs_pvd}")
    return abs_pvd


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="XDMF+H5 → PVD/VTU converter")
    parser.add_argument("--max-steps", type=int, default=None,
                        help="Limit export to the first N time steps (default: all)")
    parser.add_argument("--encoding", choices=["base64", "raw"], default="base64",
                        help="VTU data encoding: base64 (jupyterview/VTK.js) or raw (ParaView desktop)")
    parser.add_argument("--out-dir", default="output/paraview/vtu_series",
                        help="Directory for VTU files")
    parser.add_argument("--pvd", default="output/paraview/pv_output_full.pvd",
                        help="Output PVD file path")
    parser.add_argument("--h5", default="output/paraview/pv_output_full.h5",
                        help="Input HDF5 file")
    args = parser.parse_args()

    convert_xdmf_to_pvd(
        h5_file=args.h5,
        out_dir=args.out_dir,
        pvd_file=args.pvd,
        max_steps=args.max_steps,
        encoding=args.encoding,
    )
