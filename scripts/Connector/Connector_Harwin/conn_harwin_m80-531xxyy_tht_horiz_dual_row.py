#!/usr/bin/env python3
'''
kicad-footprint-generator is free software: you can redistribute it and/or
modify it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
kicad-footprint-generator is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with kicad-footprint-generator. If not, see < http://www.gnu.org/licenses/ >.
'''
import sys
import os
import math

sys.path.append(os.path.join(sys.path[0], "..", "..", ".."))  # load parent path of KicadModTree
from math import sqrt
import argparse
import yaml
from helpers import *

from KicadModTree import *
sys.path.append(os.path.join(sys.path[0], "..", "..", "tools"))  # load parent path of tools
from footprint_text_fields import addTextFields

# Basic configuration

series = 'M80'
series_long = 'Male Horizontal Through Hole Double Row 2.00mm Pitch PCB Connector'
manufacturer = 'Harwin'
datasheet = 'https://cdn.harwin.com/pdfs/M80-540.pdf'

pn = '540{n:02}xx'
number_of_rows = 2
orientation = 'H'

pitch = 2

pad_drill = 0.8
pad_size = 1.35

mount_drill = 2.4

# Pincount range for standard [and generally available] product variants
pincount_range_standard = [4, 6, 8, 10, 12, 14, 20, 26, 34, 42, 50]
# Pincount range for extended range, including semi-custom variants, that nonetheless have valid part numbers
pincount_range_extended = [4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 50]

def generate_footprint(pins, configuration):

    mpn = pn.format(n=pins)
    pins_per_row = int(pins / number_of_rows)

    # handle arguments
    orientation_str = configuration['orientation_options'][orientation]
    footprint_name = configuration['fp_name_format_string'].format(man=manufacturer,
        series=series,
        mpn=mpn, num_rows=number_of_rows, pins_per_row=pins_per_row, mounting_pad = "",
        pitch=pitch, orientation=orientation_str)

    kicad_mod = Footprint(footprint_name)
    kicad_mod.setDescription("Harwin {:s}, {:s}, {:d} Pins per row ({:s}), generated with kicad-footprint-generator".format(series_long, mpn, pins_per_row, datasheet))
    kicad_mod.setTags(configuration['keyword_fp_string'].format(series=series,
        orientation=orientation_str, man=manufacturer,
        entry=configuration['entry_direction'][orientation]))

    kicad_mod.setAttribute('smd')

    ########################## Dimensions ##############################

    A = pins - 2
    B = pins + 5
    C = pins + 10

    body_edge={
        'left': 2.4,
        'right': 8,
        'top': -((C - A) / 2),
        'bottom': A + ((C - A) / 2)
    }

    ############################# Holes ##################################
    #
    # Add mounting holes
    #
    kicad_mod.append(Pad(at=[pitch/2 - 0.15, -(B-A)/2], number="",
        type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE, size=mount_drill,
        drill=mount_drill, layers=Pad.LAYERS_NPTH))
    kicad_mod.append(Pad(at=[pitch/2 - 0.15, A + (B-A)/2], number="",
        type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE, size=mount_drill,
        drill=mount_drill, layers=Pad.LAYERS_NPTH))

    ############################# Pads ##################################
    #
    # Add pads
    #
    kicad_mod.append(PadArray(start=[0.00, 0.00], initial=1,
        pincount=pins_per_row, increment=1,  y_spacing=pitch, size=pad_size, drill=pad_drill,
        type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE, layers=Pad.LAYERS_THT))
    kicad_mod.append(PadArray(start=[pitch, 0.00], initial=pins_per_row + 1,
        pincount=pins_per_row, increment=1,  y_spacing=pitch, size=pad_size, drill=pad_drill,
        type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE, layers=Pad.LAYERS_THT))

    ######################## Fabrication Layer ###########################
    main_body_poly= [
        {'x': body_edge['left'], 'y': body_edge['top']},
        {'x': body_edge['right'], 'y': body_edge['top']},
        {'x': body_edge['right'], 'y': body_edge['bottom']},
        {'x': body_edge['left'], 'y': body_edge['bottom']},
        {'x': body_edge['left'], 'y': body_edge['top']}
    ]
    kicad_mod.append(PolygoneLine(polygone=main_body_poly,
        width=configuration['fab_line_width'], layer="F.Fab"))

    main_arrow_size= 0.4
    main_arrow_offset= -1.5
    main_arrow_poly= [
        {'x': main_arrow_offset - main_arrow_size, 'y': 0 - .4},
        {'x': main_arrow_offset, 'y': 0},
        {'x': main_arrow_offset - main_arrow_size, 'y': 0 + .4},
    ]
    kicad_mod.append(PolygoneLine(polygone=main_arrow_poly,
        width=configuration['fab_line_width'], layer="F.Fab"))

    ######################## SilkS Layer ###########################
    SilkPad_offset = (((pad_size) + configuration['silk_line_width'] ) / 2) + configuration['silk_pad_clearance']
    SilkBody_indent = 0.615    # a result of the 'overhang' on the sides of the component

    poly_silk_outline= [
        {'x': body_edge['left'] - configuration['silk_fab_offset'], 'y': -SilkPad_offset},
        {'x': body_edge['left'] - configuration['silk_fab_offset'], 'y': body_edge['top'] - configuration['silk_fab_offset'] + SilkBody_indent},
        {'x': body_edge['right'] + configuration['silk_fab_offset'], 'y': body_edge['top'] - configuration['silk_fab_offset'] + SilkBody_indent},
        {'x': body_edge['right'] + configuration['silk_fab_offset'], 'y': body_edge['bottom'] + configuration['silk_fab_offset'] - SilkBody_indent},
        {'x': body_edge['left'] - configuration['silk_fab_offset'], 'y': body_edge['bottom'] + configuration['silk_fab_offset'] - SilkBody_indent},
        {'x': body_edge['left'] - configuration['silk_fab_offset'], 'y': A + SilkPad_offset}
    ]
    kicad_mod.append(PolygoneLine(polygone=poly_silk_outline,
        width=configuration['silk_line_width'], layer="F.SilkS"))

    poly_silk_pin1_ident= [
        {'x': -(((pad_size) + configuration['silk_line_width'] ) / 2) - configuration['silk_pad_clearance'], 'y': (pad_size - configuration['silk_line_width']) / 2},
        {'x': -(((pad_size) + configuration['silk_line_width'] ) / 2) - configuration['silk_pad_clearance'], 'y': -(pad_size - configuration['silk_line_width']) / 2},
    ]
    kicad_mod.append(PolygoneLine(polygone=poly_silk_pin1_ident,
        width=configuration['silk_line_width'], layer="F.SilkS"))

    ######################## CrtYd Layer ###########################
    CrtYd_offset = configuration['courtyard_offset']['connector']
    CrtYd_grid = configuration['courtyard_grid']

    CrtYd_leftedge = -roundToBase(((pad_size/2) + CrtYd_offset),CrtYd_grid)
    CrtYd_rightedge = body_edge['right'] + CrtYd_offset
    CrtYd_topedge = body_edge['top'] - CrtYd_offset
    CrtYd_bottomedge = body_edge['bottom'] + CrtYd_offset
    CrtYd_innerleftedge = body_edge['left'] - CrtYd_offset
    CrtYd_innertopedge = -roundToBase(((pad_size/2) + CrtYd_offset),CrtYd_grid)
    CrtYd_innerbottomedge = A + roundToBase(((pad_size/2) + CrtYd_offset),CrtYd_grid)

    poly_yd_simple = [
        {'x': CrtYd_leftedge, 'y': CrtYd_topedge},
        {'x': CrtYd_rightedge, 'y': CrtYd_topedge},
        {'x': CrtYd_rightedge, 'y': CrtYd_bottomedge},
        {'x': CrtYd_leftedge, 'y': CrtYd_bottomedge},
        {'x': CrtYd_leftedge, 'y': CrtYd_topedge}
    ]

    poly_yd_complex = [
        {'x': CrtYd_innerleftedge, 'y': CrtYd_topedge},
        {'x': CrtYd_rightedge, 'y': CrtYd_topedge},
        {'x': CrtYd_rightedge, 'y': CrtYd_bottomedge},
        {'x': CrtYd_innerleftedge, 'y': CrtYd_bottomedge},
        {'x': CrtYd_innerleftedge, 'y': CrtYd_innerbottomedge},
        {'x': CrtYd_leftedge, 'y': CrtYd_innerbottomedge},
        {'x': CrtYd_leftedge, 'y': CrtYd_innertopedge},
        {'x': CrtYd_innerleftedge, 'y': CrtYd_innertopedge},
        {'x': CrtYd_innerleftedge, 'y': CrtYd_topedge}
    ]

    kicad_mod.append(PolygoneLine(polygone=poly_yd_simple,
        layer='F.CrtYd', width=configuration['courtyard_line_width']))
#    kicad_mod.append(PolygoneLine(polygone=poly_yd_complex,
#        layer='F.CrtYd', width=configuration['courtyard_line_width']))

    ######################### Text Fields ###############################
    cy1 = body_edge['top'] - configuration['courtyard_offset']['connector']
    cy2 = body_edge['bottom'] + configuration['courtyard_offset']['connector'] + 0.2

    addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=body_edge,
        courtyard={'top':cy1, 'bottom':cy2}, fp_name=footprint_name, text_y_inside_position='center', allow_rotation=True)

    ##################### Write to File and 3D ############################
    model3d_path_prefix = configuration.get('3d_model_prefix','${KISYS3DMOD}/')

    lib_name = configuration['lib_name_format_string'].format(series=series, man=manufacturer)
    model_name = '{model3d_path_prefix:s}{lib_name:s}.3dshapes/{fp_name:s}.wrl'.format(
        model3d_path_prefix=model3d_path_prefix, lib_name=lib_name, fp_name=footprint_name)
    kicad_mod.append(Model(filename=model_name))

    output_dir = '{lib_name:s}.pretty/'.format(lib_name=lib_name)
    if not os.path.isdir(output_dir): #returns false if path does not yet exist!! (Does not check path validity)
        os.makedirs(output_dir)
    filename =  '{outdir:s}{fp_name:s}.kicad_mod'.format(outdir=output_dir, fp_name=footprint_name)

    print(filename)
    file_handler = KicadFileHandler(kicad_mod)
    file_handler.writeFile(filename)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='use confing .yaml files to create footprints.')
    parser.add_argument('--global_config', type=str, nargs='?', help='the config file defining how the footprint will look like. (KLC)', default='../../tools/global_config_files/config_KLCv3.0.yaml')
    parser.add_argument('--series_config', type=str, nargs='?', help='the config file defining series parameters.', default='../conn_config_KLCv3.yaml')
    parser.add_argument('--kicad4_compatible', action='store_true', help='Create footprints kicad 4 compatible')
    args = parser.parse_args()

    with open(args.global_config, 'r') as config_stream:
        try:
            configuration = yaml.load(config_stream)
        except yaml.YAMLError as exc:
            print(exc)

    with open(args.series_config, 'r') as config_stream:
        try:
            configuration.update(yaml.load(config_stream))
        except yaml.YAMLError as exc:
            print(exc)

    configuration['kicad4_compatible'] = args.kicad4_compatible

    for pincount in pincount_range_standard:
        generate_footprint(pincount, configuration)
