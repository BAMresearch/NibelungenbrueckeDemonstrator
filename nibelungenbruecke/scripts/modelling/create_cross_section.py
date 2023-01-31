import gmsh

def create_cross_section2D(parameters):
    "Creates the cross section of the Nibelungenbrücke from a set of parameters"
    
    # Import parameters
    cs_parameters = _get_default_parameters()
    for key, value in parameters.items():
        cs_parameters[key] = value

    # Sanity checks
    _check_valid_formats(cs_parameters["output_format"])

    #### CREATE THE GEOMETRY ####
    
    #  0. Initialize gmsh
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1)

    ### 1. CREATE GEOMETRY AT THE PILOT
    
    ## 1.1 Create external geometry

    # Create a new model
    gmsh.model.add("pilot")

    # Define the dimensions of the geometry
    pilot_bottom_height=cs_parameters["pilot_bottom_height"]
    pilot_top_height=cs_parameters["pilot_top_height"]
    pilot_width=cs_parameters["pilot_width"]
    pilot_fly=cs_parameters["pilot_fly"]
    deck_thickness=cs_parameters["deck_thickness"]
    gap_length=cs_parameters["gap_length"]
    wall_thickness=cs_parameters["wall_thickness"]

    # Define the points for the line profile
    # TODO: Find better solution for the tags
    p01 = gmsh.model.geo.addPoint(-gap_length/2 - pilot_width -pilot_fly, 0, 0, tag=1)
    p03 = gmsh.model.geo.addPoint(-gap_length/2 - pilot_width, 0, 0, tag=3)
    p04 = gmsh.model.geo.addPoint(-gap_length/2 - pilot_width, -(pilot_top_height-pilot_bottom_height), 0, tag=4)
    p05 = gmsh.model.geo.addPoint(-gap_length/2 , -(pilot_top_height-pilot_bottom_height), 0, tag=5)
    p06 = gmsh.model.geo.addPoint(-gap_length/2 , 0, 0, tag=6)
    p12 = gmsh.model.geo.addPoint(gap_length/2 + pilot_width +pilot_fly, 0, 0, tag=12)
    p10 = gmsh.model.geo.addPoint(gap_length/2 + pilot_width, 0, 0, tag=10)
    p09 = gmsh.model.geo.addPoint(gap_length/2 + pilot_width, -(pilot_top_height-pilot_bottom_height), 0, tag=9)
    p08 = gmsh.model.geo.addPoint(gap_length/2 , -(pilot_top_height-pilot_bottom_height), 0, tag=8)
    p07 = gmsh.model.geo.addPoint(gap_length/2 , 0, 0, tag=7)

    # Create the lines for the pilot
    l01 = gmsh.model.geo.addLine(p01, p03, tag=1)
    l02 = gmsh.model.geo.addLine(p03, p04, tag=2)
    l03 = gmsh.model.geo.addLine(p04, p05, tag=3)
    l04 = gmsh.model.geo.addLine(p05, p06, tag=4)
    l05 = gmsh.model.geo.addLine(p06, p07, tag=5)
    l06 = gmsh.model.geo.addLine(p07, p08, tag=6)
    l07 = gmsh.model.geo.addLine(p08, p09, tag=7)
    l08 = gmsh.model.geo.addLine(p09, p10, tag=8)
    l09 = gmsh.model.geo.addLine(p10, p12, tag=9)
    l10 = gmsh.model.geo.addLine(p03, p06, tag=10)
    l11 = gmsh.model.geo.addLine(p07, p10, tag=11)

    # Synchronize the model
    gmsh.model.geo.synchronize()
    
    # Save the model
    gmsh.write(cs_parameters["output_path"]+"_pilot"+cs_parameters["output_format"])

    # Finalize gmsh
    gmsh.finalize()

    ### 2. CREATE GEOMETRY AT THE MIDDLE OF THE SPAN

    #  0. Initialize gmsh
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1)

    # Create a new model
    gmsh.model.add("span")

    # Define the dimensions of the geometry
    span_bottom_height=cs_parameters["span_bottom_height"]
    span_top_height=cs_parameters["span_top_height"]
    span_width=cs_parameters["span_width"]
    span_fly=cs_parameters["span_fly"]

    # Define the points for the line profile
    p01 = gmsh.model.geo.addPoint(-gap_length/2 - span_width -span_fly, 0, 0, tag=101)
    p03 = gmsh.model.geo.addPoint(-gap_length/2 - span_width, 0, 0, tag=103)
    p04 = gmsh.model.geo.addPoint(-gap_length/2 - span_width, -(span_top_height-span_bottom_height), 0, tag=104)
    p05 = gmsh.model.geo.addPoint(-gap_length/2 , -(span_top_height-span_bottom_height), 0, tag=105)
    p06 = gmsh.model.geo.addPoint(-gap_length/2 , 0, 0, tag=106)
    p12 = gmsh.model.geo.addPoint(gap_length/2 + span_width +span_fly, 0, 0, tag=112)
    p10 = gmsh.model.geo.addPoint(gap_length/2 + span_width, 0, 0, tag=110)
    p09 = gmsh.model.geo.addPoint(gap_length/2 + span_width, -(span_top_height-span_bottom_height), 0, tag=109)
    p08 = gmsh.model.geo.addPoint(gap_length/2 , -(span_top_height-span_bottom_height), 0, tag=108)
    p07 = gmsh.model.geo.addPoint(gap_length/2 , 0, 0, tag=107)

    # Create the lines for the span
    # l1 = gmsh.model.geo.addLine(p01, p12, tag=101)
    l01 = gmsh.model.geo.addLine(p01, p03, tag=101)
    l02 = gmsh.model.geo.addLine(p03, p04, tag=102)
    l03 = gmsh.model.geo.addLine(p04, p05, tag=103)
    l04 = gmsh.model.geo.addLine(p05, p06, tag=104)
    l05 = gmsh.model.geo.addLine(p06, p07, tag=105)
    l06 = gmsh.model.geo.addLine(p07, p08, tag=106)
    l07 = gmsh.model.geo.addLine(p08, p09, tag=107)
    l08 = gmsh.model.geo.addLine(p09, p10, tag=108)
    l09 = gmsh.model.geo.addLine(p10, p12, tag=109)
    l10 = gmsh.model.geo.addLine(p03, p06, tag=110)
    l11 = gmsh.model.geo.addLine(p07, p10, tag=111)

    # Synchronize the model
    gmsh.model.geo.synchronize()

    # Save the model
    gmsh.write(cs_parameters["output_path"]+"_span"+cs_parameters["output_format"])

    # Finalize gmsh
    gmsh.finalize()

def create_cross_section3D(parameters):
    "Creates the cross section of the Nibelungenbrücke from a set of parameters"
    
    # Import parameters
    cs_parameters = _get_default_parameters()
    for key, value in parameters.items():
        cs_parameters[key] = value

    # Sanity checks
    _check_valid_formats(cs_parameters["output_format"])

    #### CREATE THE GEOMETRY ####
    
    #  0. Initialize gmsh
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1)

    ### 1. CREATE GEOMETRY AT THE PILOT
    
    ## 1.1 Create external geometry

    # Create a new model
    gmsh.model.add("pilot")

    # Define the dimensions of the geometry
    pilot_bottom_height=cs_parameters["pilot_bottom_height"]
    pilot_top_height=cs_parameters["pilot_top_height"]
    pilot_width=cs_parameters["pilot_width"]
    pilot_fly=cs_parameters["pilot_fly"]
    pilot_hole_height = cs_parameters["pilot_hole_height"]
    deck_thickness=cs_parameters["deck_thickness"]
    gap_length=cs_parameters["gap_length"]
    wall_thickness=cs_parameters["wall_thickness"]

    # Define the points for the line profile
    # TODO: Find better solution for the tags
    p01 = gmsh.model.geo.addPoint(-gap_length/2 - pilot_width -pilot_fly, 0, 0, tag=1)
    p02 = gmsh.model.geo.addPoint(-gap_length/2 - pilot_width -pilot_fly,-deck_thickness,0, tag=2)
    p03 = gmsh.model.geo.addPoint(-gap_length/2 - pilot_width, -deck_thickness, 0, tag=3)
    p04 = gmsh.model.geo.addPoint(-gap_length/2 - pilot_width, -(pilot_top_height-pilot_bottom_height), 0, tag=4)
    p05 = gmsh.model.geo.addPoint(-gap_length/2 , -(pilot_top_height-pilot_bottom_height), 0, tag=5)
    p06 = gmsh.model.geo.addPoint(-gap_length/2 , -deck_thickness, 0, tag=6)
    p12 = gmsh.model.geo.addPoint(gap_length/2 + pilot_width +pilot_fly, 0, 0, tag=12)
    p11 = gmsh.model.geo.addPoint(gap_length/2 + pilot_width +pilot_fly, -deck_thickness, 0, tag=11)
    p10 = gmsh.model.geo.addPoint(gap_length/2 + pilot_width, -deck_thickness, 0, tag=10)
    p09 = gmsh.model.geo.addPoint(gap_length/2 + pilot_width, -(pilot_top_height-pilot_bottom_height), 0, tag=9)
    p08 = gmsh.model.geo.addPoint(gap_length/2 , -(pilot_top_height-pilot_bottom_height), 0, tag=8)
    p07 = gmsh.model.geo.addPoint(gap_length/2 , -deck_thickness, 0, tag=7)

    gmsh.model.geo.synchronize()

    gmsh.model.addPhysicalGroup(dim=0, tags=[p01,p02,p03,p04,p05,p06,p07,p08,p09,p10,p11,p12], tag=1)

    # Define the points for the hole
    ph1 =gmsh.model.geo.addPoint(-gap_length/2 - pilot_width + wall_thickness,-deck_thickness, 0, tag=201)
    ph2 =gmsh.model.geo.addPoint(-gap_length/2 - pilot_width + wall_thickness,-deck_thickness-pilot_hole_height, 0, tag=202)
    ph3 =gmsh.model.geo.addPoint(-gap_length/2 - wall_thickness,-deck_thickness-pilot_hole_height, 0, tag=203)
    ph4 =gmsh.model.geo.addPoint(-gap_length/2 - wall_thickness, -deck_thickness, 0, tag=204)
    ph8 =gmsh.model.geo.addPoint(gap_length/2 + pilot_width - wall_thickness,-deck_thickness, 0, tag=208)
    ph7 =gmsh.model.geo.addPoint(gap_length/2 + pilot_width - wall_thickness,-deck_thickness-pilot_hole_height, 0, tag=207)
    ph6 =gmsh.model.geo.addPoint(gap_length/2 + wall_thickness, -deck_thickness-pilot_hole_height, 0, tag=206)
    ph5 =gmsh.model.geo.addPoint(gap_length/2 + wall_thickness, -deck_thickness, 0, tag=205)

    gmsh.model.geo.synchronize()

    # Create a general PhysicalGroup for the points in hole 1
    gmsh.model.addPhysicalGroup(dim=0, tags=[ph1,ph2,ph3,ph4], tag=2)
    # Create a general PhysicalGroup for the points in hole 2
    gmsh.model.addPhysicalGroup(dim=0, tags=[ph5,ph6,ph7,ph8], tag=3)

    # Create the lines for the pilot
    l01 = gmsh.model.geo.addLine(p01, p02, tag=1)
    l02 = gmsh.model.geo.addLine(p02, p03, tag=2)
    l03 = gmsh.model.geo.addLine(p03, p04, tag=3)
    l04 = gmsh.model.geo.addLine(p04, p05, tag=4)
    l05 = gmsh.model.geo.addLine(p05, p06, tag=5)
    l06 = gmsh.model.geo.addLine(p06, p07, tag=6)
    l07 = gmsh.model.geo.addLine(p07, p08, tag=7)
    l08 = gmsh.model.geo.addLine(p08, p09, tag=8)
    l09 = gmsh.model.geo.addLine(p09, p10, tag=9)
    l10 = gmsh.model.geo.addLine(p10, p11, tag=10)
    l11 = gmsh.model.geo.addLine(p11, p12, tag=11)
    l12 = gmsh.model.geo.addLine(p12, p01, tag=12)

    gmsh.model.geo.synchronize()

    gmsh.model.addPhysicalGroup(dim=1, tags=[l01,l02,l03,l04,l05,l06,l07,l08,l09,l10,l11,l12], tag=1)
    pilot_curve_loop = gmsh.model.geo.addCurveLoop([l01, l02, l03, l04, l05, l06, l07, l08, l09, l10, l11, l12], reorient=True, tag = 1)

    l13 = gmsh.model.geo.addLine(ph1, ph2, tag=13)
    l14 = gmsh.model.geo.addLine(ph2, ph3, tag=14)
    l15 = gmsh.model.geo.addLine(ph3, ph4, tag=15)
    l16 = gmsh.model.geo.addLine(ph4, ph1, tag=16)
    l17 = gmsh.model.geo.addLine(ph5, ph6, tag=17)
    l18 = gmsh.model.geo.addLine(ph6, ph7, tag=18)
    l19 = gmsh.model.geo.addLine(ph7, ph8, tag=19)
    l20 = gmsh.model.geo.addLine(ph8, ph5, tag=20)

    gmsh.model.geo.synchronize()

    gmsh.model.addPhysicalGroup(dim=1, tags=[l13,l14,l15,l16], tag=2)
    gmsh.model.addPhysicalGroup(dim=1, tags=[l17,l18,l19,l20], tag=3)

    pilot_hole_loop_1 = gmsh.model.geo.addCurveLoop([l13, l14, l15, l16], reorient=True, tag = 2)
    pilot_hole_loop_2 = gmsh.model.geo.addCurveLoop([l17, l18, l19, l20], reorient=True, tag = 3)

    # Create surfaces
    gmsh.model.geo.addPlaneSurface([pilot_curve_loop, pilot_hole_loop_1, pilot_hole_loop_2], tag = 1)

    # Synchronize the model
    gmsh.model.geo.synchronize()
    
    # Save the model
    gmsh.write(cs_parameters["output_path"]+"_pilot"+cs_parameters["output_format"])

    # Finalize gmsh
    gmsh.finalize()

    ### 2. CREATE GEOMETRY AT THE MIDDLE OF THE SPAN

    #  0. Initialize gmsh
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1)

    # Create a new model
    gmsh.model.add("span")

    # Define the dimensions of the geometry
    span_bottom_height=cs_parameters["span_bottom_height"]
    span_top_height=cs_parameters["span_top_height"]
    span_width=cs_parameters["span_width"]
    span_fly=cs_parameters["span_fly"]

    # Define the points for the line profile
    p01 = gmsh.model.geo.addPoint(-gap_length/2 - span_width -span_fly, 0, 0, tag=101)
    p02 = gmsh.model.geo.addPoint(-gap_length/2 - span_width -span_fly,-deck_thickness,0, tag=102)
    p03 = gmsh.model.geo.addPoint(-gap_length/2 - span_width, -deck_thickness, 0, tag=103)
    p04 = gmsh.model.geo.addPoint(-gap_length/2 - span_width, -(span_top_height-span_bottom_height), 0, tag=104)
    p05 = gmsh.model.geo.addPoint(-gap_length/2 , -(span_top_height-span_bottom_height), 0, tag=105)
    p06 = gmsh.model.geo.addPoint(-gap_length/2 , -deck_thickness, 0, tag=106)
    p12 = gmsh.model.geo.addPoint(gap_length/2 + span_width +span_fly, 0, 0, tag=112)
    p11 = gmsh.model.geo.addPoint(gap_length/2 + span_width +span_fly, -deck_thickness, 0, tag=111)
    p10 = gmsh.model.geo.addPoint(gap_length/2 + span_width, -deck_thickness, 0, tag=110)
    p09 = gmsh.model.geo.addPoint(gap_length/2 + span_width, -(span_top_height-span_bottom_height), 0, tag=109)
    p08 = gmsh.model.geo.addPoint(gap_length/2 , -(span_top_height-span_bottom_height), 0, tag=108)
    p07 = gmsh.model.geo.addPoint(gap_length/2 , -deck_thickness, 0, tag=107)

    # Create a general PhysicalGroup for the solid points
    # gmsh.model.addPhysicalGroup(dim=0, tags=[p01,p02,p03,p04,p05,p06,p07,p08,p09,p10,p11,p12], tag=101)

    # Define the points for the hole
    ph1 =gmsh.model.geo.addPoint(-gap_length/2 - span_width + wall_thickness,-deck_thickness, 0, tag=301)
    ph2 =gmsh.model.geo.addPoint(-gap_length/2 - span_width + wall_thickness,-(span_top_height-span_bottom_height)+wall_thickness, 0, tag=302)
    ph3 =gmsh.model.geo.addPoint(-gap_length/2 - wall_thickness,-(span_top_height-span_bottom_height)+wall_thickness, 0, tag=303)
    ph4 =gmsh.model.geo.addPoint(-gap_length/2 - wall_thickness, -deck_thickness, 0, tag=304)
    ph8 =gmsh.model.geo.addPoint(gap_length/2 + span_width - wall_thickness,-deck_thickness, 0, tag=308)
    ph7 =gmsh.model.geo.addPoint(gap_length/2 + span_width - wall_thickness,-(span_top_height-span_bottom_height)+wall_thickness, 0, tag=307)
    ph6 =gmsh.model.geo.addPoint(gap_length/2 + wall_thickness, -(span_top_height-span_bottom_height)+wall_thickness, 0, tag=306)
    ph5 =gmsh.model.geo.addPoint(gap_length/2 + wall_thickness, -deck_thickness, 0, tag=305)

    # # Create a general PhysicalGroup for the points in hole 1
    # gmsh.model.addPhysicalGroup(dim=0, tags=[ph1,ph2,ph3,ph4], tag=102)
    # # Create a general PhysicalGroup for the points in hole 2
    # gmsh.model.addPhysicalGroup(dim=0, tags=[ph5,ph6,ph7,ph8], tag=103)

    # Create the lines for the span
    # l1 = gmsh.model.geo.addLine(p01, p12, tag=101)
    l01 = gmsh.model.geo.addLine(p01, p02, tag=101)
    l02 = gmsh.model.geo.addLine(p02, p03, tag=102)
    l03 = gmsh.model.geo.addLine(p03, p04, tag=103)
    l04 = gmsh.model.geo.addLine(p04, p05, tag=104)
    l05 = gmsh.model.geo.addLine(p05, p06, tag=105)
    l06 = gmsh.model.geo.addLine(p06, p07, tag=106)
    l07 = gmsh.model.geo.addLine(p07, p08, tag=107)
    l08 = gmsh.model.geo.addLine(p08, p09, tag=108)
    l09 = gmsh.model.geo.addLine(p09, p10, tag=109)
    l10 = gmsh.model.geo.addLine(p10, p11, tag=110)
    l11 = gmsh.model.geo.addLine(p11, p12, tag=111)
    l12 = gmsh.model.geo.addLine(p12, p01, tag=112)
    
    # gmsh.model.addPhysicalGroup(dim=1, tags=[l01,l02,l03,l04,l05,l06,l07,l08,l09,l10,l11,l12], tag=101)

    span_curve_loop = gmsh.model.geo.addCurveLoop([l01, l02, l03, l04, l05, l06, l07, l08, l09, l10, l11, l12], reorient=True, tag=101)

    l13 = gmsh.model.geo.addLine(ph1, ph2, tag=113)
    l14 = gmsh.model.geo.addLine(ph2, ph3, tag=114)
    l15 = gmsh.model.geo.addLine(ph3, ph4, tag=115)
    l16 = gmsh.model.geo.addLine(ph4, ph1, tag=116)
    l17 = gmsh.model.geo.addLine(ph5, ph6, tag=117)
    l18 = gmsh.model.geo.addLine(ph6, ph7, tag=118)
    l19 = gmsh.model.geo.addLine(ph7, ph8, tag=119)
    l20 = gmsh.model.geo.addLine(ph8, ph5, tag=210)

    # gmsh.model.addPhysicalGroup(dim=1, tags=[l13,l14,l15,l16], tag=102)
    # gmsh.model.addPhysicalGroup(dim=1, tags=[l17,l18,l19,l20], tag=103)

    span_hole_loop_1 = gmsh.model.geo.addCurveLoop([l13, l14, l15, l16], reorient=True, tag = 102)
    span_hole_loop_2 = gmsh.model.geo.addCurveLoop([l17, l18, l19, l20], reorient=True, tag = 103)

    # Create surfaces
    gmsh.model.geo.addPlaneSurface([span_curve_loop, span_hole_loop_1, span_hole_loop_2], tag = 101)

    # Synchronize the model
    gmsh.model.geo.synchronize()

    # Save the model
    gmsh.write(cs_parameters["output_path"]+"_span"+cs_parameters["output_format"])

    # Finalize gmsh
    gmsh.finalize()

def _get_default_parameters():

    #             span_top    |---gap_lenth---|    pilot_top
    # p01_____________________________X0______________________________p12
    # |_______________________________||_______________________________| deck_thickness
    # p02  p03|   |       |   |p06    ||    p07|   |       |   |p10  p11
    #   span_ |   |       |   |       ||       |   |       |   |  pilot_
    #   fly   |   |       |   |       ||       |   |       |   |  fly
    #         |   |       |   |_______||_______|   |       |   |
    #         |   |_______|   |       ||       |   |       |   |
    #      p04|_______________|p05    ||       |   |       |   |wall_thickness
    #              span_width         ||       |   |       |   |
    #             span_bottom         ||       |   |_______|   |
    #                                 ||    p08|_______________|p09
    #                                 ||          pilot_width
    #                                 ||          pilot_bottom
    
    default_parameters = {
        "output_path": "input/models/cross_section",
        "output_format": ".geo",
        "pilot_bottom_height": 99.328,
        "pilot_top_height": 105.849,
        "pilot_width": 2.0,
        "pilot_fly": 3.47,
        "span_bottom_height": 102.698,
        "span_top_height": 105.198,
        "span_width": 2.0,
        "span_fly": 3.15,
        "deck_thickness": 0.2,
        "gap_length": 3.70,
        "wall_thickness": 0.4
    }

    return default_parameters

def _check_valid_formats(extension):

    valid_formats = [".geo_unrolled",".msh"]
    valid_formats_str = " ".join(valid_formats)
    if extension in valid_formats:
        return
    else:
        raise Exception(f"[Cross-section creation] Output format {extension} not compatible. \
        Valid formats are {valid_formats_str}")