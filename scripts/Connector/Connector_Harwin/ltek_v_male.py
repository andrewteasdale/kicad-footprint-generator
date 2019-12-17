#!/usr/bin/env python

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

output_dir = os.getcwd()

#if specified as an argument, extract the target directory for output footprints
if len(sys.argv) > 1:
    out_dir = sys.argv[1]
    
    if os.path.isabs(out_dir) and os.path.isdir(out_dir):
        output_dir = out_dir
    else:
        out_dir = os.path.join(os.getcwd(),out_dir)
        if os.path.isdir(out_dir):
            output_dir = out_dir

if output_dir and not output_dir.endswith(os.sep):
    output_dir += os.sep
        
#import KicadModTree files
sys.path.append(os.path.join(sys.path[0], "..", "..", ".."))  # load parent path of KicadModTree
from KicadModTree import *
from KicadModTree.nodes.specialized.PadArray import PadArray
"""
footprint specific details to go here

Datasheet: http://www.jst-mfg.com/product/pdf/eng/eXH.pdf

"""
pitch = 2.0

row_pitch = 2.0

strain_relief_drill = 0.95
strain_relief_pad = 1.25

pin_drill = 0.80
pin_pad = 1.35

fab_line_width = 0.10
silk_offset = 0.1
courtyard_offset = 0.5

#FP name strings
part = "S{n:02}B-J21DK-GG" #JST part number format string	#TODO: Correct part names

name = "Harwin_LTek-Male_{r}{n:02}_P{p:.2f}mm_Vertical{supports}"

desc = "Harwin LTek Connector, {pins} pins, single row male, vertical entry{supports}"

tags = "connector harwin ltek M80"
#FP description and tags

if __name__ == '__main__':

    for rows in [1,2]:
    
        if rows == 1:
            pincount = [2,3,4,5,6,7,17,22] #number of pins in each row
            WIDTH = 4.0
        else:
            pincount = [2,3,4,5,6,7,8,9,10,13,17,22]
            WIDTH = 6.0
    
        for pins in pincount:
            
            for supports in [True,False]:
                #calculate fp dimensions
                A = (pins - 1) * pitch
                B = pins * pitch + 4.10
                
                #outline
                x1 = A/2 - B/2
                x2 = x1 + B
                
                ymid = -1 * (rows - 1) * pitch / 2
                y1 = ymid - WIDTH/2
                y2 = ymid + WIDTH/2
            
                #generate the name
                fp_name = name.format(
                    n=pins,
                    r="2x" if rows == 2 else "",
                    p=pitch,
                    supports="_StrainRelief" if supports else "")
                    
                print(fp_name)

                footprint = Footprint(fp_name)
                
                #set the FP description
                footprint.setDescription(desc.format(pins = pins * rows, supports=", strain relief clip" if supports else ''))
                
                #set the FP tags
                footprint.setTags(tags)

                # set general values
                footprint.append(Text(type='reference', text='REF**', at=[A/2,y1-1.5], layer='F.SilkS'))
                footprint.append(Text(type='value', text=fp_name, at=[A/2,y2+2], layer='F.Fab'))
                    
                #generate the pads (row 1)
                for i in range(rows):
                    footprint.append(PadArray(pincount=pins, start=[0,-i*pitch], initial=((i*pins)+1), increment=1, x_spacing=pitch, type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE, size=pin_pad, drill=pin_drill, layers=['*.Cu','*.Mask']))
                
                if supports:
                    sx1 = -2.25
                    sx2 = A + 2.25
                    sy1 = ymid - 4.75/2
                    sy2 = ymid + 4.75/2
                    
					#generate pads for strain relief
                    footprint.append(Pad(at=[sx1,sy1],type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE, size=strain_relief_pad, drill=strain_relief_drill, layers=['*.Cu','*.Mask']))
                    footprint.append(Pad(at=[sx1,sy2],type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE, size=strain_relief_pad, drill=strain_relief_drill, layers=['*.Cu','*.Mask']))
                    footprint.append(Pad(at=[sx2,sy1],type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE, size=strain_relief_pad, drill=strain_relief_drill, layers=['*.Cu','*.Mask']))
                    footprint.append(Pad(at=[sx2,sy2],type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE, size=strain_relief_pad, drill=strain_relief_drill, layers=['*.Cu','*.Mask']))
                    
					#generate top & bottom of main silk outline
                    footprint.append(Line(start=[sx1+0.5,y1-silk_offset],end=[sx2-0.5,y1-silk_offset]))
                    footprint.append(Line(start=[sx1+0.5,y2+silk_offset],end=[sx2-0.5,y2+silk_offset]))

					#generate sides of main silk outline
                    silk_endcap = [
                    {'x': sx1-0.5,'y': y2+silk_offset},
                    {'x': x1-silk_offset,'y': y2+silk_offset},
                    {'x': x1-silk_offset,'y': y1-silk_offset},
                    {'x': sx1-0.5,'y': y1-silk_offset},
                    ]              
                    footprint.append(PolygoneLine(polygone=silk_endcap))
                    footprint.append(PolygoneLine(polygone=silk_endcap,x_mirror=A/2))
                else:
                    #generate main silk outline
                    footprint.append(RectLine(start=[x1,y1],end=[x2,y2],offset=silk_offset,grid=0.05,layer='F.SilkS'))
                
				#courtyard
                footprint.append(RectLine(start=[x1,y1],end=[x2,y2],offset=courtyard_offset,grid=0.05,width=0.05,layer='F.CrtYd'))
                
                #outline on F.Fab
                footprint.append(RectLine(start=[x1,y1],end=[x2,y2],width=fab_line_width,layer='F.Fab'))
                
                #inner drawing on F.Fab
                #wall thickness
                w = 0.5
                wx = 1.75
                #inner outline
                #if rows == 1 or not supports:
                inner = [
                    {'x': -wx,'y': y1+w},
                    {'x': -wx,'y': y2-2.5*w},
                    {'x': -wx+1.5*w,'y':y2-w},
                    {'x': A+wx-1.5*w,'y':y2-w},
                    {'x': A+wx,'y': y2-2.5*w},
                    {'x': A+wx,'y': y1+w},
                    {'x': -wx,'y': y1+w},
                    ]
                    
                footprint.append(PolygoneLine(polygone=inner, layer='F.Fab', width=fab_line_width))

                off = 0.15
                bevel = [
                {'x': -wx+off,'y': y1+y2},
                {'x': -wx+off,'y': y2-2.5*w},
                {'x': -wx+1.5*w,'y': y2-w-off},
                {'x': A/2,'y': y2-w-off},
                ]
                
                footprint.append(PolygoneLine(polygone=bevel))
                footprint.append(PolygoneLine(polygone=bevel,x_mirror=A/2))
                
                #add p1 silk marker
                marker_offset = 0.45
                marker_size = 1.0
                marker_x = x1 - marker_offset
                marker_y = y2 + marker_offset
                
                marker = [
                {'x': marker_x + marker_size,'y': marker_y},
                {'x': marker_x,'y': marker_y},
                {'x': marker_x,'y': marker_y - marker_size},
                ]
                
                footprint.append(PolygoneLine(polygone=marker))
				
                #add p1 fab marker
				
                px = 0
                py = 0.75
                m = 0.25
                
                marker = [
                {'x': px,'y': py},
                {'x': px-m,'y': py+2*m},
                {'x': px+m,'y': py+2*m},
                {'x': px,'y': py},
				]
				
                footprint.append(PolygoneLine(polygone=marker, layer='F.Fab', width=fab_line_width))

				#Add Fab layer reference
                footprint.append(Text(type='user', text='%R', at=[A/2,ymid], layer='F.Fab'))				
				
                #Add a model
                footprint.append(Model(filename="${KISYS3DMOD}/Connector_Harwin.3dshapes/" + fp_name + ".wrl"))
                
                #filename
                filename = output_dir + fp_name + ".kicad_mod"
                
                file_handler = KicadFileHandler(footprint)
                file_handler.writeFile(filename)
