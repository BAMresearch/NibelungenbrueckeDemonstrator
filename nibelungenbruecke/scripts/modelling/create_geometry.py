import gmsh
import numpy as np

from nibelungenbruecke.scripts.utilities.checks import check_path_exists

def create_geometry(parameters):
    "Creates the geometry of the Nibelungenbrücke from a set of parameters and the cross-sections"
    
    # Import parameters
    geo_parameters = _get_default_parameters()
    for key, value in parameters.items():
        geo_parameters[key] = value

    # Sanity checks
    check_path_exists(geo_parameters["cross_section_path"]+"_span"+geo_parameters["cross_section_format"])
    check_path_exists(geo_parameters["cross_section_path"]+"_pilot"+geo_parameters["cross_section_format"])
    
    _check_valid_formats(geo_parameters["output_format"])
    _check_valid_extrusion(geo_parameters["extrude"])

    #### CREATE THE GEOMETRY ####
    
    #  0. Initialize gmsh and parameters
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1)

    # Create a new model
    gmsh.model.add("bridge")

    surfaces_list = []
    # Import cross-section geometries

    # Span
    gmsh.merge(geo_parameters["cross_section_path"]+"_span"+geo_parameters["cross_section_format"])
    points_span = gmsh.model.getEntities(0)
    lines_span = gmsh.model.getEntities(1)
    if geo_parameters["extrude"] == "surfaces":
        surface_span = gmsh.model.getEntities(2)
        surfaces_list.append(surface_span[0][1])

    # Pilot
    gmsh.merge(geo_parameters["cross_section_path"]+"_pilot"+geo_parameters["cross_section_format"])
    points_pilot = [new_point for new_point in gmsh.model.getEntities(0) if not new_point in points_span]
    lines_pilot = [new_line for new_line in gmsh.model.getEntities(1) if not new_line in lines_span]
    if geo_parameters["extrude"] == "surfaces":
        surface_pilot = [new_surf for new_surf in gmsh.model.getEntities(2) if not new_surf in surface_span]
        surfaces_list.append(surface_pilot[0][1])

    # Initialize physical groups dictionaries
    points_physical_groups_dict = {}
    for point in gmsh.model.getEntities(0):
        try:
            points_physical_groups_dict[point[1]]=gmsh.model.getPhysicalGroupsForEntity(point[0], point[1])[0]
        except IndexError:
            pass
    lines_physical_groups_dict = {}
    for line in gmsh.model.getEntities(1):
        try:
            lines_physical_groups_dict[line[1]]=gmsh.model.getPhysicalGroupsForEntity(line[0], line[1])[0]
        except IndexError:
            pass

    if geo_parameters["extrude"] == "surfaces":
        surf_physical_groups_dict = {} 
        try:
            for surf in gmsh.model.getEntities(2):
                surf_physical_groups_dict[surf[1]]=1

        except IndexError:
            pass
    ### SAMPLER

    def sampler(n, length, mode):
        x = np.linspace(0, length, n)
        if mode == "linear":
            y = np.zeros(n)
            for i in range(n):
                if x[i] < length/2:
                    y[i] = (x[i]/(length/2))
                else:
                    y[i] = 1-((x[i]-(length/2))/(length/2))
        elif mode == "parabolic":
            y = 1-((x-length/2)/(length/2))**2
        else:
            raise ValueError("Invalid mode. Choose 'linear' or 'parabolic'.")
        return y

    interpolation_coords_x = sampler(geo_parameters["number_of_divisions"], geo_parameters["length"] ,"linear")
    interpolation_coords_y = sampler(geo_parameters["number_of_divisions"], geo_parameters["length"] ,geo_parameters["interpolation"])
    interpolation_coords_z = np.linspace(0,geo_parameters["length"],geo_parameters["number_of_divisions"])

    interpolation_coordinates = (interpolation_coords_x, interpolation_coords_y, interpolation_coords_z)
   
    dx = {}
    dy = {}
    dz = {}

    # Calculate the director vector for each point
    for point_pilot, point_span, points_id in zip(points_pilot, points_span, range(len(points_pilot))):
        dx[points_id], dy[points_id], dz[points_id] = _calculate_extrude_vector(point_pilot, point_span, interpolation_coordinates)
    
    # Delete span section to prevent duplicates or inconsistent behaviour
    if geo_parameters["extrude"] == "surfaces":
        gmsh.model.geo.remove(surface_span, recursive=True)
        surfaces_list = surfaces_list[1:]
    gmsh.model.geo.remove(lines_span, recursive= True)
    gmsh.model.geo.remove(points_span)
    gmsh.model.geo.synchronize()

    old_cross_section_points = points_pilot
    old_cross_section_lines = lines_pilot

    grouped_points = {}
    grouped_cs_lines = {}
    grouped_z_lines = {}
    # Iterate over sections
    for section in range(len(dz[0])):
        new_cross_section_points = []
        new_cross_section_lines = []
        new_surfaces = []
        # Extrude the cross-section to the new points
        for point, point_id in zip(old_cross_section_points, dz.keys()):
            newDimTags = gmsh.model.geo.extrude([point],dx[point_id][section],dy[point_id][section],dz[point_id][section])
            new_cross_section_points += [newDimTags[0]]
            points_physical_groups_dict[newDimTags[0][1]] = points_physical_groups_dict[point[1]]
            grouped_points[point[1]] = newDimTags[0][1]
            grouped_z_lines[point[1]] = newDimTags[1][1]
        
        # Create the wireframe of the new cross-section and update
        for start, end, line  in [(gmsh.model.getBoundary([line])[0],gmsh.model.getBoundary([line])[1], line) for line in old_cross_section_lines]:
            cs_line= [(1,gmsh.model.geo.addLine(grouped_points[start[1]],grouped_points[end[1]]))]
            new_cross_section_lines += cs_line
            lines_physical_groups_dict[cs_line[0][1]] = lines_physical_groups_dict[line[1]]
            grouped_cs_lines[grouped_points[start[1]]] = cs_line[0][1]

        # Create the closed loops and surfaces of the section
        for old_cs_line, new_cs_line in zip(old_cross_section_lines, new_cross_section_lines):
            start_old, end_old = gmsh.model.getBoundary([old_cs_line])
            curve_loop = gmsh.model.geo.addCurveLoop([-old_cs_line[1],grouped_z_lines[start_old[1]],new_cs_line[1],-grouped_z_lines[end_old[1]]],reorient= True)
            if geo_parameters["extrude"] == "surfaces":
                surfaces_list.append(gmsh.model.geo.addPlaneSurface([curve_loop]))
                surf_physical_groups_dict[surfaces_list[-1]] = lines_physical_groups_dict[old_cs_line[1]]

        # Update and synchronize
        old_cross_section_lines = new_cross_section_lines
        old_cross_section_points = new_cross_section_points
        gmsh.model.geo.synchronize()

    if geo_parameters["extrude"] == "surfaces":
        # Group elements per physical group
        grouped_dict_points = {value: [point for point, group in points_physical_groups_dict.items() if group == value] for value in set(points_physical_groups_dict.values())}
        grouped_dict_lines = {value: [line for line, group in lines_physical_groups_dict.items() if group == value] for value in set(lines_physical_groups_dict.values())}
        grouped_dict_surfs = {value: [surf for surf, group in surf_physical_groups_dict.items() if group == value] for value in set(surf_physical_groups_dict.values())}

        # Create end cross-section
        end_holes = []
        end_hole_curveloops = []
        for hole_group_id in geo_parameters["physical_group_tag_pilot_holes"]: 
            hole_i_list =[]
            for line in new_cross_section_lines:
                if lines_physical_groups_dict[line[1]] == hole_group_id:
                    hole_i_list.append(line[1])
            end_holes.append(hole_i_list)
            end_hole_curveloops.append(gmsh.model.geo.addCurveLoop(hole_i_list, reorient=True))
        end_external = [element[1] for element in new_cross_section_lines if element not in end_holes[:]]
        end_external_curveloop = gmsh.model.geo.addCurveLoop(end_external, reorient=True)

        end_lines_curveloops = [end_external_curveloop] + end_hole_curveloops
        end_surface_cs = gmsh.model.geo.addPlaneSurface(end_lines_curveloops)

        #Create surface loops and volume
        hole_surface_loops_list = []
        for hole_group_id in geo_parameters["physical_group_tag_pilot_holes"]: 
            hole_surface_loops_list.append(gmsh.model.geo.addSurfaceLoop(grouped_dict_surfs.pop(hole_group_id)))

        external_surfaces = []   
        for key, val in grouped_dict_surfs.items():
            external_surfaces.append(val)
        external_surfaces = external_surfaces[0] + [end_surface_cs]
        external_surface_loops = gmsh.model.geo.addSurfaceLoop(external_surfaces)
        volume_surfaceloops = [external_surface_loops] + hole_surface_loops_list
        volume = gmsh.model.geo.addVolume(volume_surfaceloops)


    # Remove duplicates
    gmsh.model.geo.removeAllDuplicates()
    gmsh.model.geo.synchronize()

    # Create a general PhysicalGroup for the volume
    volumes = gmsh.model.getEntities(dim=3)
    volumes_tags = [volume_i[1] for volume_i in volumes]
    gmsh.model.addPhysicalGroup(dim=3, tags=volumes_tags, tag=42)

    # Create a general PhysicalGroup for the surfaces
    surfaces = gmsh.model.getEntities(dim=2)
    surface_tags = [surface_i[1] for surface_i in surfaces]
    gmsh.model.addPhysicalGroup(dim=2, tags=surface_tags, tag=42)

     # Add the lines to the general PhysicalGroup
    lines = gmsh.model.getEntities(dim=1)
    line_tags = [line_i[1] for line_i in lines]
    gmsh.model.addPhysicalGroup(dim=1, tags=line_tags, tag=42)

    # Save the model
    gmsh.write(geo_parameters["output_path"]+geo_parameters["output_format"])

    # Finalize gmsh
    gmsh.finalize()

       
def _get_default_parameters():

    default_parameters = {
        "cross_section_path": "input/models/cross_section",
        "cross_section_format": ".geo_unrolled",
        "length": 95.185,
        "number_of_divisions": 31,
        "interpolation": "parabolic",
        "output_path": "input/models/geometry",
        "output_format": ".geo_unrolled",
        "extrude": "surfaces",
        "physical_group_tag_pilot_holes": []
    }

    return default_parameters

def _calculate_extrude_vector(point_pilot, point_span, interpolation_coordinates):

    # Retrieve span and pilot coords
    x_span, y_span, z_span = gmsh.model.getValue(point_span[0],point_span[1],[])
    x_pilot, y_pilot,z_pilot = gmsh.model.getValue(point_pilot[0],point_pilot[1],[])

    # Calculate extrusion director vectors
    dx = [(x_span-x_pilot)*int_coord for int_coord in np.diff(interpolation_coordinates[0])]
    dy = [(y_span-y_pilot)*int_coord for int_coord in np.diff(interpolation_coordinates[1])]
    dz = [int_coord for int_coord in np.diff(interpolation_coordinates[2])]

    return dx, dy, dz

def _check_valid_formats(extension):

    valid_formats = [".geo_unrolled",".msh"]
    valid_formats_str = " ".join(valid_formats)
    if extension in valid_formats:
        return
    else:
        raise Exception(f"[Geometry creation] Output format {extension} not compatible. \
        Valid formats are {valid_formats_str}")


def _check_valid_extrusion(extrusion):

    valid_formats = ["surfaces","lines"]
    valid_formats_str = " ".join(valid_formats)
    if extrusion in valid_formats:
        return
    else:
        raise Exception(f"[Geometry creation] Extrude mode {extrusion} not defined. \
        Valid modes are {valid_formats_str}")