#  (c) 2014 by Piotr Adamowicz (MadMinstrel)

# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Meltdown baking extended",
    "author": "Piotr Adamowicz, Stephen Leger",
    "version": (0, 3),
    "blender": (2, 7, 7),
    "location": "Properties Editor -> Render Panel",
    "description": "Improved baking UI",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "https://github.com/s-leger/meltdown/issues",
    "category": "Baking"}

import code
import os
import bpy
from bpy.types import PropertyGroup, Operator, Panel
from bpy.props import BoolProperty, IntProperty, EnumProperty, FloatProperty, StringProperty, CollectionProperty, PointerProperty
from bpy.utils import register_class, unregister_class
from progress_report import ProgressReport

class BakePair(PropertyGroup):
    activated = BoolProperty(name = "Activated", description="Pair on/off", default = True)
    lowpoly = StringProperty(name="", description="Lowpoly mesh", default="")
    cage = StringProperty(name="", description="Cage mesh", default="")
    highpoly = StringProperty(name="", description="Highpoly mesh", default="")
    hp_obj_vs_group = EnumProperty(name="Object vs Group", description="", default="OBJ", items = [('OBJ', '', 'Object', 'MESH_CUBE', 0), ('GRP', '', 'Group', 'GROUP', 1)])
    extrusion_vs_cage = EnumProperty(name="Extrusion vs Cage", description="", default="EXT", items = [('EXT', '', 'Extrusion', 'OUTLINER_DATA_META', 0), ('CAGE', '', 'Cage', 'OUTLINER_OB_LATTICE', 1)])
    extrusion = FloatProperty(name="Extrusion", description="", default=0.5, min=0.0)
    use_hipoly = BoolProperty(name="Use Hipoly", default = True)
    no_materials = BoolProperty(name="No Materials", default = False)
    
def normal_items(self, context):
    if self.engine == "CYCLES":
        return (("TANGENT","Tangent",""),
                ("OBJECT", "Object", ""))
    else:
        return (("TANGENT","Tangent",""),
                 ("OBJECT", "Object", ""),
                 ("WORLD", "World", ""),
                 ("CAMERA", "Camera", ""))

enum_file_formats = (('BMP','.bmp',""), ('PNG','.png',""), ('JPEG','.jpg',""), ('TARGA','.tga',""), ('TIFF', '.tif',""), ('OPEN_EXR','.exr',""))

def pass_name_items(self, context):
    if self.engine == "CYCLES":
        return (("COMBINED","Combined",""),
                ("MAT_ID","Material ID",""),
                ("SHADOW","Shadow",""),
                ("AO","Ambient Occlusion",""),
                ("NORMAL","Normal",""),
                ("UV","UV",""),
                ("EMIT","Emission",""),
                ("ENVIRONMENT","Environment",""),
                ("DIFFUSE","DIffuse",""),
                ("GLOSSY","Glossy",""),
                ("TRANSMISSION","Transmission",""),
                ("SUBSURFACE","Subsurface",""))
    else:
        return  (("SPEC_COLOR","Specular colors",""),
                ("SPEC_INTENSITY","Specular intensity", ""),
                ("MIRROR_COLOR","Mirror colors",""),
                ("MIRROR_INTENSITY","Mirror intensity",""),
                ("ALPHA","Alpha",""),
                ("EMIT","Emission",""),
                ("VERTEX_COLORS","Vertex colors",""),
                ("DERIVATIVE","Derivative",""),
                ("DISPLACEMENT","Displacement",""),
                ("TEXTURE","Textures",""),
                ("NORMALS","Normals",""),
                ("SHADOW","Shadow",""),
                ("AO","Ambient occlusion",""),
                ("FULL","Full render",""),
                ("Z","Z depth",""),
                ("MATERIAL_INDEX","Material index",""),
                ("OBJECT_INDEX","Object index",""),
                ("UV", "UV", ""),
                ("MIST","Mist", "")
                )
                
''' BLENDER_RENDER 
                   bake
                   bake_aa_mode
                   bake_bias
                   bake_distance
                   bake_margin
                   bake_normal_space
                   bake_quad_split
                   bake_samples
                   bake_type
                   bake_user_scale
                   
                   ‘COMBINED’, ‘Z’, ‘COLOR’, ‘DIFFUSE’, ‘SPECULAR’, ‘SHADOW’, ‘AO’, 
                   ‘REFLECTION’, ‘NORMAL’, ‘VECTOR’, ‘REFRACTION’, ‘OBJECT_INDEX’, 
                   ‘UV’, ‘MIST’, ‘EMIT’, ‘ENVIRONMENT’, ‘MATERIAL_INDEX’, 
                   ‘DIFFUSE_DIRECT’, ‘DIFFUSE_INDIRECT’, ‘DIFFUSE_COLOR’, 
                   ‘GLOSSY_DIRECT’, ‘GLOSSY_INDIRECT’, ‘GLOSSY_COLOR’, 
                   ‘TRANSMISSION_DIRECT’, ‘TRANSMISSION_INDIRECT’, ‘TRANSMISSION_COLOR’, 
                   ‘SUBSURFACE_DIRECT’, ‘SUBSURFACE_INDIRECT’, ‘SUBSURFACE_COLOR’                  
'''                
                
class BakePass(PropertyGroup):
    activated = BoolProperty(name = "Activated", default = True)
    pair_counter = IntProperty(name="Pair Counter", description="", default=0)
    engine =  EnumProperty(name = "Renderer", default = "CYCLES",
                                    items = (("CYCLES","Cycles",""),
                                            ("BLENDER_RENDER","Blender Internal","")))
    pass_name = EnumProperty(name = "Bake type",
                                            items=pass_name_items)  
                                           
    influence = FloatProperty(name="Texture influence", description="BI texture influence", default=1.0, min=0.0)    
    material_override = StringProperty(name="Material Override", description="", default="")
    ao_distance = FloatProperty(name="Distance", description="", default=10.0, min=0.0)
    samples = IntProperty(name="Samples", description="", default=1)
    clean_environment = BoolProperty(name = "Clean Environment", default = False)
    
    # cycles baking props
    environment_highpoly = BoolProperty(name = "All Highpoly", default = False)
    environment_group = StringProperty(name="", description="Environment", default="")
     
    nm_space = EnumProperty(name = "Normal map space",
                                    items = normal_items)

    normal_r = EnumProperty(name="R", description="", default="POS_X", 
                                    items = (("POS_X", "X+", ""), 
                                            ("NEG_X", "X-", ""),
                                            ("POS_Y", "Y+", ""),
                                            ("NEG_Y", "Y-", ""),
                                            ("POS_Z", "Z+", ""),
                                            ("NEG_Z", "Z-", "")))
    normal_g = EnumProperty(name="G", description="", default="POS_Y", 
                                    items = (("POS_X", "X+", ""), 
                                            ("NEG_X", "X-", ""),
                                            ("POS_Y", "Y+", ""),
                                            ("NEG_Y", "Y-", ""),
                                            ("POS_Z", "Z+", ""),
                                            ("NEG_Z", "Z-", "")))
    normal_b = EnumProperty(name="B", description="", default="POS_Z", 
                                    items = (("POS_X", "X+", ""), 
                                            ("NEG_X", "X-", ""),
                                            ("POS_Y", "Y+", ""),
                                            ("NEG_Y", "Y-", ""),
                                            ("POS_Z", "Z+", ""),
                                            ("NEG_Z", "Z-", "")))
    #'AO', 'EMIT', 'DIRECT', 'INDIRECT', 'DIFFUSE', 'GLOSSY', 'TRANSMISSION', 'SUBSURFACE'
    cycles_direct = BoolProperty(name = "Direct", default = True)
    cycles_indirect = BoolProperty(name = "Indirect", default = True)
    cycles_color = BoolProperty(name = "Color", default = True)
    cycles_combi_ao = BoolProperty(name = "AO", default = True)
    cycles_combi_emit = BoolProperty(name = "Emit", default = True)
    cycles_combi_diffuse = BoolProperty(name = "Diffuse", default = True)
    cycles_combi_glossy = BoolProperty(name = "Glossy", default = True)
    cycles_combi_transmission = BoolProperty(name = "Transmission", default = True)
    cycles_combi_subsurface = BoolProperty(name = "Subsurface", default = True)
    bi_normalized  = BoolProperty(name = "Normalized", default = False)      
    bi_multires  = BoolProperty(name = "Bake from Multires", default = False)
    
    def get_pass_fullname(self):
        pass_fullname = self.pass_name
        pass_filter = self.get_pass_filter()    
        for filter in ["DIRECT","INDIRECT","COLOR"]:
            if filter in pass_filter:
                pass_fullname += "_" + filter
        return pass_fullname
        
    def get_pass_filter(self):
        pass_filter = set()
        
        if self.engine != "CYCLES":
            return pass_filter
            
        if self.pass_name == "COMBINED":
            for attr in dir(self):
                if hasattr(self, attr) and "cycles_combi_" in attr and getattr(self, attr):
                    pass_filter.add(attr[13:].upper())
                   
        if self.pass_name in ["COMBINED", "DIFFUSE", "GLOSSY", "SUBSURFACE", "TRANSMISSION"]:        
            if self.cycles_direct:
                pass_filter.add("DIRECT")
            if self.cycles_indirect:
                pass_filter.add("INDIRECT")
            if self.cycles_color and self.pass_name != "COMBINED":
                pass_filter.add("COLOR")
        
        if len(pass_filter) < 1:
            pass_filter.add('NONE')
        
        return pass_filter
    
    def draw(self, layout, expand=True):
        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        if expand:
            row.prop(self, 'engine')
        else:
            row.prop(self, 'engine', "")
        layout.separator()
        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        if expand:
            row.prop(self, 'pass_name')
        else:
            row.prop(self, 'pass_name', "")
        layout.separator()
        
        if expand:
            if self.engine == 'CYCLES':
                if self.pass_name in ["SUBSURFACE","TRANSMISSION","GLOSSY","DIFFUSE"]:
                    row = layout.row(align=True)
                    row.alignment = 'EXPAND'
                    row.prop(self, "cycles_direct", toggle=True)
                    row.prop(self, "cycles_indirect",  toggle=True)
                    row.prop(self, "cycles_color",  toggle=True)
                    
                if self.pass_name == "COMBINED":
                    row = layout.row(align=True)
                    row.alignment = 'EXPAND'
                    row.prop(self, "cycles_direct",  toggle=True)
                    row.prop(self, "cycles_indirect",  toggle=True)
                    row = layout.row(align=True)
                    row.prop(self, "cycles_combi_diffuse")
                    row.prop(self, "cycles_combi_subsurface")
                    row = layout.row(align=True)
                    row.prop(self, "cycles_combi_glossy")
                    row.prop(self, "cycles_combi_ao")
                    row = layout.row(align=True)
                    row.prop(self, "cycles_combi_transmission")
                    row.prop(self, "cycles_combi_emit")
                
                row = layout.row(align=True)
                    
                if self.pass_name == "NORMAL":
                    row.prop(self, "nm_space")
                    layout.separator()
                    row = layout.row(align=True)
                    row.alignment = 'EXPAND'
                    row.label(text="Swizzle")
                    row.prop(self, 'normal_r', text = "")
                    row.prop(self, 'normal_g', text = "")
                    row.prop(self, 'normal_b', text = "")
                else:
                    row.prop(self, "samples")
            

                if self.pass_name == "AO":
                    row = layout.row(align=True)
                    row.alignment = 'EXPAND'
                    row.prop(self, "ao_distance")
            
            if self.engine == 'BLENDER_RENDER':
                if self.pass_name in ["DERIVATIVE","DISPLACEMENT","NORMALS","AO"]:
                    row = layout.row(align=True)
                    row.alignment = 'EXPAND'
                    row.prop(self, "bi_multires")
                    
                if self.pass_name in ["DISPLACEMENT","NORMALS","AO"]:
                    row = layout.row(align=True)
                    row.alignment = 'EXPAND'
                    row.prop(self, "bi_normalized")
                    
                if self.pass_name == "NORMALS":
                    row = layout.row(align=True)
                    row.alignment = 'EXPAND'
                    row.prop(self, "nm_space")
                    
            row = layout.row(align=True)
            row.alignment = 'EXPAND'
            row.prop(self, 'influence')
                
            if self.pass_name in ["FULL", "SPEC_COLOR", "SPEC_INTENSITY", "MIRROR_COLOR", "MIRROR_INTENSITY", "COMBINED", "SHADOW", "AO", "DIFFUSE", "GLOSSY"]:
                row = layout.row(align=True)
                row.alignment = 'EXPAND'
                row.prop(self, "clean_environment")
                if not self.clean_environment:
                    row = layout.row(align=True)
                    row.alignment = 'EXPAND'
                    row.prop(self, 'environment_highpoly')  
                    if not self.environment_highpoly:
                        row = layout.row(align=True)
                        row.alignment = 'EXPAND'
                        row.prop_search(self, "environment_group", bpy.data, "groups", text = "Environment")
                    
    def get_cycles_pass_type(self):
        # pass_type, pass_filter
        if self.pass_name == "MAT_ID": return "DIFFUSE", {'COLOR'}
        return self.pass_name, self.get_pass_filter()
        
    def get_blend_mode(self):
        pass_fullname = self.get_pass_fullname()
        if "COLOR" in pass_fullname or self.pass_name in ["SHADOW","AO"]:
            return 'MULTIPLY'
        if "DIRECT" in pass_fullname or "INTENSITY" in pass_fullname:
            return 'ADD'
        return 'MIX'
    
    def get_fileext(self, job):
        format = job.output_format
        for formats in enum_file_formats:
            if formats[0] == format:
                return formats[1]
        
    def get_filepath(self, job, pair):
        path = job.output 
        if path[-1:] != os.path.sep:
            path = path + os.path.sep
        path = path + bpy.path.clean_name(pair.lowpoly, "_")
        pass_fullname = self.get_pass_fullname()
        if len(pass_fullname)>0:
            path += "_" + pass_fullname.lower()
        path += self.get_fileext(job)
        return path

    def get_filename(self, job, pair):
        name = bpy.path.clean_name(pair.lowpoly, "_")
        pass_fullname = self.get_pass_fullname()
        if len(pass_fullname)>0:
            name += "_" + pass_fullname.lower()
        name += self.get_fileext(job)
        return name        
  
class BakeJob(PropertyGroup):
    activated = BoolProperty(name = "Activated", default = True)
    expand = BoolProperty(name = "Expand", default = True)
    resolution_x = IntProperty(name="Resolution X", default = 1024)
    resolution_y = IntProperty(name="Resolution Y", default = 1024)
    antialiasing = BoolProperty(name="4x Antialiasing", description="", default=False)
    aa_sharpness = FloatProperty(name="AA Sharpness", description="", default=0.5, min = 0.0, max = 1.0)
    
    margin = IntProperty(name="Margin", default = 16, min = 0)
    
    output = StringProperty(name = 'File path',
                            description = 'The path of the output image.',
                            default = '//textures/',
                            subtype = 'FILE_PATH')
    output_format = EnumProperty(name="Format", 
        description = 'The file format of the output images.',
        items=enum_file_formats, 
        default="PNG")
    pairs = CollectionProperty(type=BakePair)
    bakepasses = CollectionProperty(type=BakePass)
    
    def get_render_resolution(self):
        if self.antialiasing == True:
            return [self.resolution_x * 2, self.resolution_y * 2]
        else:
            return [self.resolution_x, self.resolution_y]
        
        
class MeltdownSettings(PropertyGroup):
    bl_idname = __name__
    jobs = CollectionProperty(type=BakeJob)

class MeltdownBakeOp(Operator):
    '''Process baking jobs'''

    bl_idname = "meltdown.bake"
    bl_label = "Start Baking"
    
    job = IntProperty()
    bakepass = IntProperty()
    pair = IntProperty()

    bake_all = BoolProperty()
    bake_target = StringProperty()
    
    def remove_baked_mat(self, scene):
        for obj in scene.objects:
            for name, slot in obj.material_slots.items():
                slot.link = 'OBJECT'
                slot.material = None
                slot.link = 'DATA'
                
    def create_temp_tex(self, bakepass, lowpoly):
        
        tex = None
        
        for bake_mat in lowpoly.data.materials:
            lowpoly.active_material = bake_mat
            break;
        if bakepass.engine == 'BLENDER_RENDER':
            for uvtex in lowpoly.data.uv_textures:
                if uvtex.active_render:
                    uvtex.active = True
                    for d in uvtex.data:
                        d.image = bpy.data.images["MDtarget"]
        else:
            #add an image node to every lowpoly model's materials
            for bake_mat in lowpoly.data.materials:
                
                # add other engines here
 
                bake_mat.use_nodes = True
                if "MDtarget" not in bake_mat.node_tree.nodes:
                    tex = bake_mat.node_tree.nodes.new(type = "ShaderNodeTexImage")
                    tex.name = 'MDtarget'          
                else:
                    tex = bake_mat.node_tree.nodes["MDtarget"]
                
                tex.image = bpy.data.images["MDtarget"]
                bake_mat.node_tree.nodes.active = tex
                
                    
            if tex is not None:
                bake_mat = lowpoly.active_material
                bake_mat.node_tree.nodes.active = tex
                    
    # 1
    def create_render_target(self, job):
        bpy.ops.image.new(name="MDtarget", width= job.get_render_resolution()[0], \
        height = job.get_render_resolution()[1], \
        color=(0.0, 0.0, 0.0, 0.0), alpha=True, generated_type='BLANK', float=False)
        
    def cleanup_render_target(self, job, bakepass, pair):
        baketarget = bpy.data.images["MDtarget"]
        
        # call compo trees here
        self.compo_nodes_margin(job, bakepass, pair, baketarget)
        
        #unlink from image editors
        for wm in bpy.data.window_managers:
            for window in wm.windows:
                for area in window.screen.areas:
                    if area.type == "IMAGE_EDITOR":
                        area.spaces[0].image = None
        
    # def apply_modifiers(self):
    
    # def merge_group(self):
    
    def scene_copy(self, scene):
        # store the original names of things in the scene so we can easily identify them later
        for object in scene.objects:
            object["md_orig_name"] = object.name
        
        attrs = ["materials", "textures", "images", "groups", "worlds"]
        for attr in attrs:
            blocks = getattr(bpy.data, attr)
            for block in blocks:
                block["md_orig_name"] = block.name
        
        # duplicate the scene
        bpy.ops.scene.new(type='FULL_COPY')
        tmp_scene = bpy.context.scene
        tmp_scene.name = "MD_TMP"
        tmp_scene.layers[0] = True
         
        # From here, context.scene is "MD_TMP"
        
        # tag the copied object names with _MD_TMP
        for object in tmp_scene.objects:
            object.name = object["md_orig_name"] + "_MD_TMP"
        
        for attr in attrs:
            blocks = getattr(bpy.data, attr)
            for block in blocks:
                if block["md_orig_name"] != block.name:
                    block.name = block["md_orig_name"] + "_MD_TMP"
                    
        # unique name for world settings as we do use it when setting up scene        
        for block in bpy.data.worlds:
            if block["md_orig_name"] != block.name:
                block.name = "MD_TMP"
               
        return tmp_scene
            
    def copy_engine_settings(self, scene, job, bakepass):
        #copy pass settings to cycles settings
        
        if bakepass.engine == 'CYCLES':
            bake_type, pass_filter = bakepass.get_cycles_pass_type()
            scene.cycles.bake_type = bake_type
            scene.cycles.samples = bakepass.samples
            bpy.data.worlds["MD_TMP"].light_settings.distance = bakepass.ao_distance
        
        if bakepass.engine == 'BLENDER_RENDER':
            scene.render.bake_type = bakepass.pass_name
            scene.render.bake_samples = bakepass.samples
            scene.render.bake_margin = job.margin
            scene.render.bake_normal_space = bakepass.nm_space
            
        # add other engines here
    
    
    def pass_material_id_prep(self, scene, pair):
        
        def change_material(hp):
            for slot in hp.material_slots:
                mat = slot.material
                mat.use_nodes = True
                
                tree = mat.node_tree
                
                for node in tree.nodes:
                    tree.nodes.remove(node)
                
                tree.nodes.new(type = "ShaderNodeBsdfDiffuse")
                tree.nodes.new(type = "ShaderNodeOutputMaterial")
                output = tree.nodes["Diffuse BSDF"].outputs["BSDF"]
                input = tree.nodes["Material Output"].inputs["Surface"]
                tree.links.new(output, input)
                
                tree.nodes["Diffuse BSDF"].inputs["Color"].default_value = \
                [mat.diffuse_color[0], mat.diffuse_color[1], mat.diffuse_color[2], 1]
        
        
        if pair.highpoly != "":
            if pair.hp_obj_vs_group == "GRP":
                for object in bpy.data.groups[pair.highpoly+"_MD_TMP"].objects:
                    change_material(object)
            else:
                change_material(hp = scene.objects[pair.highpoly+"_MD_TMP"])
            
            
    def prepare_multires(self, scene, job, bakepass, pair):
        # Build a highpoly setup from lowpoly with multires modifier
        
        object = scene.objects[pair.lowpoly+"_MD_TMP"]
        for mod in object.modifiers:
            if mod.type == 'MULTIRES':
                pair.use_hipoly = True
                highpoly = object.copy()
                highpoly.data = object.data.copy()
                pair.highpoly = pair.lowpoly + "_MULTIRES_HI"
                highpoly.name = pair.highpoly + "_MD_TMP"
                scene.objects.link(highpoly)
                for himod in highpoly.modifiers:
                    if himod.type == 'MULTIRES':
                        himod.levels = max(mod.levels, mod.sculpt_levels, mod.render_levels)
                        scene.objects.active = highpoly
                        bpy.ops.object.modifier_apply( modifier=himod.name)
            # setup lowpoly modifier
            mod.levels = min(mod.levels, mod.sculpt_levels, mod.render_levels) 
            bpy.ops.object.modifier_apply( modifier=mod.name) 
            #mod.render_level = mod.level    
    
    def use_object(self, object):
        object.hide = False
        object.hide_select = False
        object.hide_render = False
        object.layers[0] = True
        object.select = True
    # 4       
    def prepare_scene(self, scene, job, bakepass, pair):
        
        
        self.copy_engine_settings(scene, job, bakepass)
        
        # make selections, ensure visibility
        bpy.ops.object.select_all(action='DESELECT')
        
        
        if pair.highpoly != "":
            if pair.hp_obj_vs_group == "GRP":
                for object in bpy.data.groups[pair.highpoly+"_MD_TMP"].objects:
                    self.use_object(object)
            else:
                object = self.tmp_scene.objects[pair.highpoly+"_MD_TMP"]
                self.use_object(object)
        else:
            pair.use_hipoly = False
        
        #lowpoly visibility
        lowpoly = scene.objects[pair.lowpoly+"_MD_TMP"]
        self.use_object(lowpoly)
        scene.objects.active = lowpoly
        
        #cage visibility
        if pair.cage != "":
            cage = scene.objects[pair.cage+"_MD_TMP"]
            cage.hide = True
            cage.hide_render = True
        
        if not bakepass.clean_environment:
            if bakepass.environment_highpoly:
                # iterate over objects designated as highpoly and select them
                for pair in job.pairs:
                    if pair.hp_obj_vs_group == "GRP":
                        for object in  bpy.data.groups[pair.highpoly+"_MD_TMP"].objects:
                            self.use_object(object)
                    else:
                        object = scene.objects[pair.highpoly+"_MD_TMP"]
                        self.use_object(object)
            else:
                # select objects in environment group if set
                if bakepass.environment_group != "":
                    for object in bpy.data.groups[bakepass.environment_group+"_MD_TMP"].objects:
                        self.use_object(object)
        
        # remove unnecessary objects
        if bakepass.environment_group != "" \
        or bakepass.clean_environment \
        or bakepass.environment_highpoly: #do not remove if environment group empty
            for object in scene.objects:
                if object.select == False:
                    self.remove_object(object)
        
        # cycles based material id pass
        if bakepass.pass_name == "MAT_ID":
            self.pass_material_id_prep(scene, pair)

    # 3 bake a pair
    def bake_set(self, scene, job, bakepass, pair):
        
        no_materials = False
        
        #ensure lowpoly has material
        lowpoly = scene.objects[pair.lowpoly+"_MD_TMP"]
        
        if len(lowpoly.data.materials) == 0 \
            or lowpoly.material_slots[0].material == None:
            no_materials = True
            temp_mat = bpy.data.materials.new("Meltdown_MD_TMP")
            # use nodes by default for cycles only
            temp_mat.use_nodes = bakepass.engine != "BLENDER_RENDER"
            lowpoly.data.materials.append(temp_mat)
            lowpoly.active_material = temp_mat
        
        #lowpoly.select = True
        #scene.objects.active = lowpoly
        self.create_temp_tex(bakepass, lowpoly)
        
        if pair.extrusion_vs_cage == "CAGE":
            pair_use_cage = True
        else:
            pair_use_cage = False
        
        clear = True
        if bakepass.pair_counter > 0:
            clear = False
        bakepass.pair_counter = bakepass.pair_counter + 1
       
        #bake
        
        if bakepass.engine == 'BLENDER_RENDER':
            bpy.ops.object.bake_image()
        
        if bakepass.engine == 'CYCLES':      
            bake_type, pass_filter = bakepass.get_cycles_pass_type()          
            bpy.ops.object.bake(type=bake_type, pass_filter=pass_filter, \
            filepath="", \
            width=job.get_render_resolution()[0], height=job.get_render_resolution()[1], margin=0, \
            use_selected_to_active=pair.use_hipoly, cage_extrusion=pair.extrusion, cage_object=pair.cage, \
            normal_space=bakepass.nm_space, \
            normal_r=bakepass.normal_r, normal_g=bakepass.normal_g, normal_b=bakepass.normal_b, \
            save_mode='INTERNAL', use_clear=clear, use_cage=pair_use_cage, \
            use_split_materials=False, use_automatic_name=False)
      
    # 2
    def bake_pass(self, progress, src_scene, job, bakepass):
        
        #the pair counter is used to determine whether to clear the image
        #set it to 0 after each bake pass
        bakepass.pair_counter = 0
        
        # Tag baked objects
        for pair in job.pairs:
            if pair.activated:
                src_scene.objects[pair.lowpoly]["bake_object"] = True
                
        # Switch engine and material sources
        bpy.ops.meltdown.switch_materials(engine=bakepass.engine, link='DATA',all_objects=False)
        pairs = [pair for pair in job.pairs if pair.activated]
        progress.enter_substeps(len(pairs))
                    
        for pair in pairs: 
            progress.step()  
            self.create_render_target(job)    
            tmp_scene = self.scene_copy(src_scene)
            #self.remove_baked_mat(tmp_scene)
            self.prepare_multires(tmp_scene, job, bakepass, pair)
            self.prepare_scene(tmp_scene, job, bakepass, pair)
            self.bake_set(tmp_scene, job, bakepass, pair)
            self.cleanup(tmp_scene)
            self.cleanup_render_target(job, bakepass, pair)
        progress.leave_substeps()
        
    def remove_object(self, object):
                
        if bpy.data.objects.find(object.name) > -1:
            
            data = object.data
            name = data.name
            
            bpy.data.scenes["MD_TMP"].objects.unlink(object)
            bpy.data.objects.remove(object)
            
            attrs = ["meshes", "lamps", "cameras", "curves", "texts", "metaballs", "lattices", "armatures", "speakers"]
            for attr in attrs:
                blocks = getattr(bpy.data, attr)
                if blocks.find(name) > -1:
                    if not data.users:
                        blocks.remove(data)
                    return 
        
    def cleanup(self, scene):
        
        # realy clean up everything, still left to check for particles
        
        attrs = ["materials", "textures", "images", "groups"]
        
        for object in scene.objects:
            self.remove_object(object)
            
        for object in bpy.data.objects:
            del object["md_orig_name"]
            
        for attr in attrs:
            blocks = getattr(bpy.data, attr)
            for block in blocks:
                if block.name.endswith("MD_TMP"):
                    blocks.remove(block)
                else:
                    del block["md_orig_name"]
        
        # Dirty hack to clean world's user - as i don't know who is using it
        bpy.data.worlds["MD_TMP"].user_clear()
        bpy.data.worlds.remove(bpy.data.worlds["MD_TMP"])
        
        bpy.ops.scene.delete()
           
    def compo_nodes_margin(self, job, bakepass, pair, targetimage):
       
        bpy.ops.scene.new(type = "EMPTY")
        bpy.context.scene.name = "MD_COMPO"
        scene = bpy.context.scene
        
        # make sure the compositor is using nodes
        scene.use_nodes = True
        scene.render.resolution_x = job.resolution_x
        scene.render.resolution_y = job.resolution_y
        scene.render.resolution_percentage = 100
        scene.render.filepath = bakepass.get_filepath(job, pair)
        scene.render.image_settings.compression = 0
        scene.render.image_settings.file_format = job.output_format
        
        tree = scene.node_tree
        
        # get rid of all nodes
        for node in tree.nodes:
            tree.nodes.remove(node)
        
        # make a dictionary of all the nodes we're going to need
        # the vector is for placement only, otherwise useless
        nodes = {
            "Image": ["CompositorNodeImage", (-900.0, 100.0)],
            "Inpaint": ["CompositorNodeInpaint", (-700.0, 100.0)],
            "Filter": ["CompositorNodeValue", (-700.0, -100.0)],
            "Negative": ["CompositorNodeMath", (-700.0, -300.0)],
            "TF1": ["CompositorNodeTransform", (-500.0, 100.0)],
            "TF2": ["CompositorNodeTransform", (-500.0, -100.0)],
            "TF3": ["CompositorNodeTransform", (-500.0, -300.0)],
            "TF4": ["CompositorNodeTransform", (-500.0, -500.0)],
            "Mix1": ["CompositorNodeMixRGB", (-300.0, 100.0)],
            "Mix2": ["CompositorNodeMixRGB", (-300.0, -300.0)],
            "Mix3": ["CompositorNodeMixRGB", (-100.0, 100.0)],
            "Output": ["CompositorNodeComposite", (200.0, 100.0)]
        }
        
        # add all the listed nodes
        for key, node_data in nodes.items():
            node = tree.nodes.new(type = node_data[0])
            node.location = node_data[1]
            node.name = key
            node.label = key
            
        links = [
            ["Image", "Image", "Inpaint", "Image"],
            ["Filter", "Value", "Negative", 1],
            ["Inpaint", "Image", "TF1", "Image"],
            ["Inpaint", "Image", "TF2", "Image"],
            ["Inpaint", "Image", "TF3", "Image"],
            ["Inpaint", "Image", "TF4", "Image"],
            ["Filter", "Value", "TF1", 2],
            ["Filter", "Value", "TF2", 1],
            ["Filter", "Value", "TF2", 2],
            ["Filter", "Value", "TF4", 1],
            ["Negative", "Value", "TF1", 1],
            ["Negative", "Value", "TF3", 1],
            ["Negative", "Value", "TF3", 2],
            ["Negative", "Value", "TF4", 2],
            ["TF1", "Image", "Mix1", 1],
            ["TF2", "Image", "Mix1", 2],
            ["TF3", "Image", "Mix2", 1],
            ["TF4", "Image", "Mix2", 2],
            ["Mix1", "Image", "Mix3", 1],
            ["Mix2", "Image", "Mix3", 2],
            ["Mix3", "Image", "Output", "Image"]
        ]
        
        for link in links:
            output = tree.nodes[link[0]].outputs[link[1]]
            input = tree.nodes[link[2]].inputs[link[3]]
            tree.links.new(output, input)

        if job.antialiasing == True:
            margin = job.margin*2
            filter_width = (1.0-job.aa_sharpness)/2.0
            print("filter "+str(filter_width))
            transform_scale = 0.5
        else:
            margin = job.margin
            filter_width = 0.0            
            transform_scale = 1.0
        
        tree.nodes["Image"].image = targetimage
        tree.nodes["Inpaint"].distance = margin
        tree.nodes["Filter"].outputs[0].default_value = filter_width
        tree.nodes["Negative"].inputs[0].default_value = 0.0
        tree.nodes["Negative"].operation = "SUBTRACT"
        tree.nodes["TF1"].inputs[4].default_value = transform_scale
        tree.nodes["TF2"].inputs[4].default_value = transform_scale
        tree.nodes["TF3"].inputs[4].default_value = transform_scale
        tree.nodes["TF4"].inputs[4].default_value = transform_scale
        tree.nodes["TF1"].filter_type = "BICUBIC"
        tree.nodes["TF2"].filter_type = "BICUBIC"
        tree.nodes["TF3"].filter_type = "BICUBIC"
        tree.nodes["TF4"].filter_type = "BICUBIC"
        tree.nodes["Mix1"].inputs[0].default_value = 0.5
        tree.nodes["Mix2"].inputs[0].default_value = 0.5
        tree.nodes["Mix3"].inputs[0].default_value = 0.5
        
        bpy.ops.render.render(write_still = True, scene = "MD_COMPO")
        bpy.ops.scene.delete()
    
    def execute(self, context):
        
        src_scene = context.scene
        jobs = [job for job in src_scene.meltdown_settings.jobs if job.activated]
        wm = context.window_manager
        if len(jobs) < 1:
            self.report({'INFO'}, "No job found in queue, use Add job.")
            return {"FINISHED"}
            
        with ProgressReport(wm) as progress:  # Not giving a WindowManager here will default to console printing.
            progress.enter_substeps(len(jobs))
            for job in jobs:
                
                # ensure save path exists
                if not os.path.exists(bpy.path.abspath(job.output)):
                    os.makedirs(bpy.path.abspath(job.output))
                    
                bakepasses = [bakepass for bakepass in job.bakepasses if bakepass.activated]
                progress.enter_substeps(len(bakepasses))
                    
                for bakepass in bakepasses:
                    self.bake_pass(progress, src_scene, job, bakepass)
                
                progress.leave_substeps()
                
            bpy.data.images["MDtarget"].user_clear()
            bpy.data.images.remove(bpy.data.images["MDtarget"])
            
            # Create material with baked maps
            bpy.ops.meltdown.create_baked_material()
            
            # Show up result
            bpy.ops.meltdown.switch_materials(engine='BLENDER_RENDER', link='OBJECT',all_objects=False)
            progress.leave_substeps("Finished !")
        

        
        return {'FINISHED'}

class MeltdownAddPairOp(Operator):
    '''add pair'''

    bl_idname = "meltdown.add_pair"
    bl_label = "Add Pair"
    
    job_index = IntProperty()
    def execute(self, context):
        context.scene.meltdown_settings.jobs[self.job_index].pairs.add()
        return {'FINISHED'}

class MeltdownRemPairOp(Operator):
    '''delete pair'''

    bl_idname = "meltdown.rem_pair"
    bl_label = "Remove Pair"
    
    pair_index = IntProperty()
    job_index = IntProperty()
    def execute(self, context):
        context.scene.meltdown_settings.jobs[self.job_index].pairs.remove(self.pair_index)
        
        return {'FINISHED'}
        
class MeltdownAddPassOp(Operator):
    '''add pass'''

    bl_idname = "meltdown.add_pass"
    bl_label = "Add Pass"
    
    job_index = IntProperty()
    def execute(self, context):
        context.scene.meltdown_settings.jobs[self.job_index].bakepasses.add()
        return {'FINISHED'}

class MeltdownRemPassOp(Operator):
    '''delete pass'''

    bl_idname = "meltdown.rem_pass"
    bl_label = "Remove Pass"
    
    pass_index = IntProperty()
    job_index = IntProperty()
    def execute(self, context):
        context.scene.meltdown_settings.jobs[self.job_index].bakepasses.remove(self.pass_index)
        return {'FINISHED'}

class MeltdownAddJobOp(Operator):
    '''add job'''

    bl_idname = "meltdown.add_job"
    bl_label = "Add Bake Job"
    
    def execute(self, context):
        context.scene.meltdown_settings.jobs.add()
        return {'FINISHED'}

class MeltdownRemJobOp(Operator):
    '''delete job'''

    bl_idname = "meltdown.rem_job"
    bl_label = "Remove Bake Job"
    
    job_index = IntProperty()
    def execute(self, context):
        context.scene.meltdown_settings.jobs.remove(self.job_index)
        return {'FINISHED'}

class MeltdownUnwrap(Operator):
    '''unwrap'''

    bl_idname = "meltdown.unwrap"
    bl_label = "Auto Unwrap"
    def execute(self, context):
        wm = context.window_manager
        scene = context.scene
        setup = scene.meltdown_setup
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        ob = bpy.context.active_object
        mesh = ob.data
        ob.update_from_editmode()
        seams = 0
        for e in mesh.edges:
            if e.use_seam:
                seams = 1
                break
        if seams:
            name = 'Auto-Unwrap'
            bpy.ops.uv.unwrap()
            self.report({'INFO'}, "Reset UVS using your marked seams.")
        else: 
            if setup.auto_unwrap == 'SMART':
                name = 'Auto-Smart'
                p = setup.smart_unwrap
                bpy.ops.uv.smart_project(angle_limit=p.angle_limit, island_margin=p.island_margin, user_area_weight=p.user_area_weight, \
                                         use_aspect=p.use_aspect, stretch_to_bounds=p.stretch_to_bounds)
                self.report({'INFO'}, "Reset UVS using Smart UV Project.")
        
            if setup.auto_unwrap == 'LIGHTMAP':
                name = "Auto-Lightmap"
                p = setup.lightmap_unwrap
                bpy.ops.uv.lightmap_pack(PREF_CONTEXT=p.PREF_CONTEXT, PREF_PACK_IN_ONE=p.PREF_PACK_IN_ONE, PREF_NEW_UVLAYER=p.PREF_NEW_UVLAYER, \
                                         PREF_APPLY_IMAGE=p.PREF_APPLY_IMAGE, PREF_IMG_PX_SIZE=p.PREF_IMG_PX_SIZE, PREF_BOX_DIV=p.PREF_BOX_DIV, \
                                         PREF_MARGIN_DIV=p.PREF_MARGIN_DIV)
                self.report({'INFO'}, "Reset UVS using Lightmap pack.")
        ob.data.uv_textures[len(ob.data.uv_textures)-1].name = name
        ob.data.uv_textures[len(ob.data.uv_textures)-1].active = True
        bpy.ops.object.mode_set(mode='OBJECT')
        return {'FINISHED'}

class MeltdownMakeClearSetupPassOp(Operator):
    '''Setup pass jobs for selection'''

    bl_idname = "meltdown.clear_setup"
    bl_label = "Clear jobs"
    
    def execute(self, context):
        scene = context.scene
        scene.meltdown_settings.jobs.clear()        
        return {'FINISHED'}
        
class MeltdownMakeSetupPassOp(Operator):
    '''Setup pass jobs for selection'''

    bl_idname = "meltdown.add_setup"
    bl_label = "Add job"
    
    def execute(self, context):
        scene = context.scene
        objs = [obj for obj in context.selected_objects if obj.type == 'MESH']
        settings = scene.meltdown_setup
        meltdown_settings = scene.meltdown_settings
        #meltdown_settings.jobs.clear()
        
        # each job share objects and pass settings
        job = meltdown_settings.jobs.add()
        job.expand = False
        job.output = settings.output
        job.output_format = settings.output_format
        job.antialiasing = settings.antialiasing
        job.resolution_x = settings.resolution_x
        job.resolution_y = settings.resolution_y
        
        for obj in objs:
            if not obj.data.uv_textures:
                scene.objects.active = obj
                bpy.ops.meltdown.unwrap()            
            pair = job.pairs.add()
            pair.lowpoly = obj.name
        
        for bake_pass in settings.bakepasses:
            new_bake_pass = job.bakepasses.add()
            for attr in dir(bake_pass):
                if hasattr(bake_pass, attr):
                    try:
                        setattr(new_bake_pass, attr, getattr(bake_pass, attr))
                    except:
                        pass
        
        return {'FINISHED'}
       
class MeltdownSwitchMaterialOp(Operator):
    '''Switch engine and materials'''

    bl_idname = "meltdown.switch_materials"
    bl_label = "Switch materials"
    engine = EnumProperty(name = "Renderer", default = "CYCLES",
                                    items = (("CYCLES","Cycles",""),
                                            ("BLENDER_RENDER","Blender Internal","")))
    link = EnumProperty(name="Link", 
                                    items=(("DATA","Data",""),("OBJECT","Object","")),
                                    default="DATA")
    all_objects = BoolProperty(name="All Objects", default=False)
    
    def get_store_prop_name(self, scene):
        prop_name = None
        if scene.render.engine == 'CYCLES':
            prop_name = "cycles_use_nodes"
        if scene.render.engine == 'BLENDER_RENDER':
            prop_name = "bi_use_nodes"
        return prop_name
        
    def store_material_use_nodes(self, scene):    
        prop_name = self.get_store_prop_name(scene)
        if prop_name is not None:
            for obj in scene.objects:
                if self.all_objects or "bake_object" in obj:
                   for name, slot in obj.material_slots.items():
                        mat = slot.material
                        if mat is not None:
                            if mat.use_nodes:
                                mat[prop_name] = mat.use_nodes
                            else:
                                if prop_name in mat:
                                    del mat[prop_name]
    
    def restore_material_use_nodes(self, scene):
        prop_name = self.get_store_prop_name(scene)
        if prop_name is not None:
            for obj in scene.objects:
                if self.all_objects or "bake_object" in obj:
                   for name, slot in obj.material_slots.items():
                        mat = slot.material
                        if mat is not None:
                            mat.use_nodes = prop_name in mat
                                
    def switch_material_link(self, scene):
        for obj in scene.objects:
            if self.all_objects or "bake_object" in obj:
               for name, slot in obj.material_slots.items():
                    slot.link = self.link
                
    def switch_engine(self, scene):
        scene.render.engine = self.engine
    
    def execute(self, context):
        scene = context.scene
        self.store_material_use_nodes(scene)
        self.switch_material_link(scene)
        self.switch_engine(scene)
        self.restore_material_use_nodes(scene)
        return {'FINISHED'}
        
class MeltdownEnableCyclesMaterialOp(Operator):
    '''Show Cycles materials'''

    bl_idname = "meltdown.enable_cycles"
    bl_label = "Cycles"
        
    def execute(self, context):
        bpy.ops.meltdown.switch_materials(engine='CYCLES', link='DATA')
        context.scene.meltdown_setup.material_mode = 'CYCLES'
        return {'FINISHED'}

class MeltdownEnableBiMaterialOp(Operator):
    '''Show bi materials'''

    bl_idname = "meltdown.enable_bi"
    bl_label = "Blender"
    
    def execute(self, context):
        bpy.ops.meltdown.switch_materials(engine='BLENDER_RENDER', link='DATA')
        context.scene.meltdown_setup.material_mode = 'BLENDER_RENDER'
        return {'FINISHED'} 
              
class MeltdownEnableBakedMaterialOp(Operator):
    '''Show baked materials'''

    bl_idname = "meltdown.enable_baked"
    bl_label = "Baked"
    
    def execute(self, context):
        bpy.ops.meltdown.switch_materials(engine='BLENDER_RENDER', link='OBJECT')
        context.scene.meltdown_setup.material_mode = 'BAKED'
        return {'FINISHED'}    

class MeltdownMakeBIMaterialOp(Operator):
    '''Setup rendered images in Blender Internal maps'''

    bl_idname = "meltdown.create_baked_material"
    bl_label = "Use rendered maps in BI"
    
    def execute(self, context):
        scene = context.scene
        jobs  = scene.meltdown_settings.jobs
        for job in jobs:
            for pair in job.pairs:
                obj = scene.objects[pair.lowpoly]
                obj["bake_object"] = True
                
                mat = None
                for name, slot in obj.material_slots.items():
                    slot.link = 'OBJECT'
                    if slot.material is not None:
                        mat = slot.material
                        break
                        
                if mat is None:
                    mat = bpy.data.materials.new(name=pair.lowpoly+"_BakeResult")
                
                mat.diffuse_color = (0,0,0)
                mat.use_shadeless = True
                
                for i, slot in enumerate(mat.texture_slots):
                    if slot is not None:
                        mat.texture_slots.clear(i)
                bakepasses = self.sort_bake_passes(job.bakepasses)

                # Setup Blender Internal material with baked maps
                for j, bake_pass in enumerate(bakepasses):
                    slot = self.find_empty_slot(mat)
                    filename = bake_pass.get_filename(job, pair)
                    filepath = bake_pass.get_filepath(job, pair)
                    tex = bpy.data.textures.new(name=filename, type='IMAGE')
                    img_idx = bpy.data.images.find(filename)
                    if img_idx > -1:
                        image = bpy.data.images[img_idx]
                        image.reload()
                    else:
                        image = bpy.data.images.load(filepath)
                    tex.image = image
                    self.config_texture_slot(bake_pass, slot, tex, image)
                    slot.texture = tex
                    
                # assign baked result material to object
                for name, slot in obj.material_slots.items():
                    slot.link = 'OBJECT'
                    slot.material = mat
                    slot.link = 'DATA'
                    """    
                    # Configure original materials nodes replacement 
                    for orig in materials:
                        if orig is not None and orig != mat:
                            orig.use_nodes = True
                            out_id = orig.node_tree.nodes.find("Output")
                            if out_id > -1:
                                nout = orig.node_tree.nodes[out_id]
                            else:
                                nout = orig.node_tree.nodes.new(type="ShaderNodeOutput")
                            nmat_id = orig.node_tree.nodes.find(pair.lowpoly+"_BakeResult")
                            if nmat_id > -1:
                                nmat = orig.node_tree.nodes[nmat_id]
                            else:
                                nmat = orig.node_tree.nodes.new(type="ShaderNodeMaterial")
                                nmat.name = pair.lowpoly+"_BakeResult"
                            nmat.material = mat
                            orig.node_tree.links.new(nmat.outputs[0], nout.inputs[0])
                    """   

        scene.meltdown_setup.material_mode = 'BAKED'
        
        return {'FINISHED'}
    
    def find_empty_slot(self, mat):
        for slot in mat.texture_slots:
            if slot is None:
                return mat.texture_slots.add()
            else:
                if slot.texture is None:
                    return slot
        return mat.texture_slots.add()
     
    def config_texture_slot(self, bake_pass, slot, tex, image):
    
        slot.blend_type = bake_pass.get_blend_mode()
        
        if 'DIFFUSE' in bake_pass.pass_name or bake_pass.pass_name in ['COMBINED','SHADOW','AO','TEXTURE','FULL']:
            slot.use_map_color_diffuse = True
            slot.diffuse_color_factor = bake_pass.influence
        else:
            slot.use_map_color_diffuse = False
            
        if 'EMIT' in bake_pass.pass_name:  
            slot.use_map_emit = True
            slot.emit_factor = bake_pass.influence
            
        if 'GLOSSY' in bake_pass.pass_name or 'SPEC_COLOR' in bake_pass.name:
            slot.use_map_color_spec = True
            slot.specular_color_factor = bake_pass.influence
            
        if 'SPEC_INTENSITY' in bake_pass.pass_name:
            slot.use_map_specular = True
            slot.specular_factor = bake_pass.influence
        
        if 'NORMAL' in bake_pass.pass_name:
            image.colorspace_settings.name = "Non-Color"
            slot.use_map_normal = True
            slot.normal_factor = bake_pass.influence
           
    def get_pass_order(self, bakepass):
        pass_fullname = bakepass.get_pass_fullname()
        return [ "COMBINED_DIRECT", "COMBINED_INDIRECT", "COMBINED_DIRECT_INDIRECT", "FULL", "TEXTURE",\
          "DIFFUSE_INDIRECT", "DIFFUSE_DIRECT", "DIFFUSE_DIRECT_INDIRECT", "DIFFUSE_COLOR", \
          "SPEC_INTENSITY", "SPEC_COLOR", \
          "MIRROR_INTENSITY", "MIRROR_COLOR", \
          "DIFFUSE_DIRECT_COLOR", "DIFFUSE_INDIRECT_COLOR", "DIFFUSE_DIRECT_INDIRECT_COLOR", \
          "GLOSSY_DIRECT", "GLOSSY_INDIRECT",  "GLOSSY_DIRECT_INDIRECT", "GLOSSY_COLOR", \
          "GLOSSY_DIRECT_COLOR", "GLOSSY_INDIRECT_COLOR", "GLOSSY_DIRECT_INDIRECT_COLOR", \
          "TRANSMISSION_DIRECT", "TRANSMISSION_INDIRECT",  "TRANSMISSION_DIRECT_INDIRECT", "TRANSMISSION_COLOR", \
          "TRANSMISSION_DIRECT_COLOR", "TRANSMISSION_INDIRECT_COLOR", "TRANSMISSION_DIRECT_INDIRECT_COLOR", \
          "SUBSURFACE_DIRECT", "SUBSURFACE_INDIRECT",  "SUBSURFACE_DIRECT_INDIRECT", "SUBSURFACE_COLOR", \
          "SUBSURFACE_DIRECT_COLOR", "SUBSURFACE_INDIRECT_COLOR", "SUBSURFACE_DIRECT_INDIRECT_COLOR", \
          "ENVIRONMENT", "EMIT", "AO", "SHADOW", "NORMAL", "UV", "MAT_ID", \
          "MATERIAL_INDEX", "OBJECT_INDEX", "NORMALS", "DISPLACEMENT", "DERIVATIVE", "Z", "ALPHA", "VERTEX_COLORS"
          ].index(pass_fullname)
          
    def sort_bake_passes(self, bakepasses):
        return sorted(bakepasses, key=self.get_pass_order)

class SmartUnwrapProps(PropertyGroup):
    bl_idname = 'meltdown.smart_unwrap'
    
    angle_limit = FloatProperty(name="Angle Limit", description="", default=66, min = 1.0, max = 89.0)
    island_margin = FloatProperty(name="Island Margin", description="", default=0, min = 0.0, max = 1.0)
    user_area_weight = FloatProperty(name="Area Weight", description="", default=0, min = 0.0, max = 1.0)
    use_aspect = BoolProperty(name = "Correct Aspect", default = True)
    stretch_to_bounds = BoolProperty(name = "Stretch to UV Bounds", default = True)
    
    def draw(self, layout):
        row = layout.row()
        row.prop(self,"angle_limit")
        row = layout.row()
        row.prop(self,"island_margin")
        row = layout.row()
        row.prop(self,"user_area_weight")
        row = layout.row()
        row.prop(self,"use_aspect")
        row = layout.row()
        row.prop(self,"stretch_to_bounds")
        
class LightmapUnwrapProps(PropertyGroup):
    bl_idname = 'meltdown.lightmap_unwrap'
    
    PREF_CONTEXT = EnumProperty(
            name="Selection",
            default="ALL_FACES",
            items=(('SEL_FACES', "Selected Faces", "Space all UVs evenly"),
                   ('ALL_FACES', "All Faces", "Average space UVs edge length of each loop"),
                   ('ALL_OBJECTS', "Selected Mesh Object", "Average space UVs edge length of each loop")
                   ),
            )

    # Image & UVs...
    PREF_PACK_IN_ONE = BoolProperty(
            name="Share Tex Space",
            description=("Objects Share texture space, map all objects "
                         "into 1 uvmap"),
            default=True,
            )
    PREF_NEW_UVLAYER = BoolProperty(
            name="New UV Map",
            description="Create a new UV map for every mesh packed",
            default=False,
            )
    PREF_APPLY_IMAGE = BoolProperty(
            name="New Image",
            description=("Assign new images for every mesh (only one if "
                         "shared tex space enabled)"),
            default=False,
            )
    PREF_IMG_PX_SIZE = IntProperty(
            name="Image Size",
            description="Width and Height for the new image",
            min=64, max=5000,
            default=512,
            )
    # UV Packing...
    PREF_BOX_DIV = IntProperty(
            name="Pack Quality",
            description="Pre Packing before the complex boxpack",
            min=1, max=48,
            default=12,
            )
    PREF_MARGIN_DIV = FloatProperty(
            name="Margin",
            description="Size of the margin as a division of the UV",
            min=0.001, max=1.0,
            default=0.1,
            ) 
    def draw(self, layout):
        row = layout.row()
        row.prop(self,"PREF_CONTEXT")
        row = layout.row()
        row.prop(self,"PREF_PACK_IN_ONE")
        row = layout.row()
        row.prop(self,"PREF_NEW_UVLAYER")
        #row = layout.row()
        #row.prop(self,"PREF_APPLY_IMAGE")
        #row = layout.row()
        #row.prop(self,"PREF_IMG_PX_SIZE")
        row = layout.row()
        row.prop(self,"PREF_BOX_DIV")
        row = layout.row()
        row.prop(self,"PREF_MARGIN_DIV")
   
class MeltdownSetup(PropertyGroup):
    bl_idname = 'meltdown.setup_properties'
    auto_unwrap = EnumProperty(name="Unwrap", description="", default="SMART", 
        items = (('SMART', 'Smart uv', ''),
                 ('LIGHTMAP', 'Lightmap', '')))
    
    lightmap_unwrap = PointerProperty(type=LightmapUnwrapProps)
    smart_unwrap = PointerProperty(type=SmartUnwrapProps)
    
    expand = BoolProperty(name = "Expand", default = True)
    resolution_x = IntProperty(name="Resolution X", default = 1024)
    resolution_y = IntProperty(name="Resolution Y", default = 1024)
    antialiasing = BoolProperty(name="4x Antialiasing", description="", default=False)
    aa_sharpness = FloatProperty(name="AA Sharpness", description="", default=0.5, min = 0.0, max = 1.0)
    
    margin = IntProperty(name="Margin", default = 16, min = 0)
    
    output = StringProperty(name = 'File path',
                            description = 'The path of the output images.',
                            default = '//textures/',
                            subtype = 'FILE_PATH')
    output_format = EnumProperty(name="Format", 
        description = 'The file format of the output images.',
        items=enum_file_formats, 
        default="PNG")
    bakepasses = CollectionProperty(type=BakePass)
    material_mode = EnumProperty(name="Show materials", items=(("CYCLES","Cycles",""),("BLENDER_RENDER","Blender Internal",""),("BAKED","Baked bi","")))
    
class MeltdownAddSetupPassOp(Operator):
    '''add pass'''

    bl_idname = "meltdown.add_setup_pass"
    bl_label = "Add Pass"
    
    def execute(self, context):
        scene_name = bpy.context.scene.name
        bpy.data.scenes[scene_name].meltdown_setup.bakepasses.add()
        return {'FINISHED'}
        
class MeltdownRemSetupPassOp(Operator):
    '''delete pass'''

    bl_idname = "meltdown.rem_setup_pass"
    bl_label = "Remove Pass"
    
    pass_index = IntProperty()
    def execute(self, context):
        scene_name = bpy.context.scene.name
        bpy.data.scenes[scene_name].meltdown_setup.bakepasses.remove(self.pass_index)
        return {'FINISHED'}
        
class MeltdownSetupPanel(bpy.types.Panel):
    bl_label = "Baking setup"
    bl_idname = "OBJECT_PT_meltdown_setup"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "Baking"    
    
    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "CYCLES" or context.scene.render.engine == "BLENDER_RENDER"
    
    def draw(self, context):
        layout = self.layout
        edit = context.user_preferences.edit
        wm = context.window_manager
        setup = context.scene.meltdown_setup
        box = layout.box()
        row = box.row(align=True)
        row.prop(setup, "auto_unwrap")
        
        if setup.auto_unwrap == 'SMART':
            setup.smart_unwrap.draw(box)
        if setup.auto_unwrap == 'LIGHTMAP':
            setup.lightmap_unwrap.draw(box)
            
        box = layout.box()
        row = box.row(align=True)
        row.label(text="Resolution")
        row = box.row(align=True)
        row.alignment = 'EXPAND'
        row.prop(setup, 'resolution_x', text="X")
        row.prop(setup, 'resolution_y', text="Y")      
        row = box.row(align=True)
        row.alignment = 'EXPAND'
        row.prop(setup, 'antialiasing', text="4x Antialiasing")
        if setup.antialiasing == True:
            row = box.row(align=True)
            row.alignment = 'EXPAND'
            row.prop(setup, 'aa_sharpness', text="AA sharpness")
        row = box.row(align=True)
        row.alignment = 'EXPAND'
        row.prop(setup, 'margin', text="Margin")
        row = box.row(align=True)
        row.alignment = 'EXPAND'
        row.prop(setup, 'output', text="Path")
        row = box.row(align=True)
        row.alignment = 'EXPAND'
        row.prop(setup, 'output_format', text="Format")
        
        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        if setup.expand == False: 
            row.prop(setup, "expand", icon="TRIA_RIGHT", icon_only=True, text="Passes", emboss=False)
            for pass_i, bakepass in enumerate(setup.bakepasses):
                row = layout.row(align=True)
                row.alignment = 'EXPAND'
                
                bakepass.draw(row, expand=False)

                col = row.column()
                rem = col.operator("meltdown.rem_setup_pass", text = "", icon = "X")
                rem.pass_index = pass_i
                col = row.column()
                if bakepass.activated:
                    col.prop(bakepass, "activated", icon_only=True, icon = "RESTRICT_RENDER_OFF", emboss = False)
                else:
                    col.prop(bakepass, "activated", icon_only=True, icon = "RESTRICT_RENDER_ON", emboss = False)

        else:
            row.prop(setup, "expand", icon="TRIA_DOWN", icon_only=True, text="Passes", emboss=False)
                
            for pass_i, bakepass in enumerate(setup.bakepasses):
                row = layout.row(align=True)
                row.alignment = 'EXPAND'
                box = row.box().column(align=True)
                box.separator()
                bakepass.draw(box)
                col = row.column()
                row = col.row()
                rem = row.operator("meltdown.rem_setup_pass", text = "", icon = "X")
                rem.pass_index = pass_i
                
                row = col.row()
                if bakepass.activated:
                    row.prop(bakepass, "activated", icon_only=True, icon = "RESTRICT_RENDER_OFF", emboss = False)
                else:
                    row.prop(bakepass, "activated", icon_only=True, icon = "RESTRICT_RENDER_ON", emboss = False)

        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        row.operator("meltdown.add_setup_pass", icon = "ZOOMIN")
        row.separator()
        box = layout.box()
        row = box.row(align=True)
        row.alignment = 'EXPAND'
        row.operator("meltdown.add_setup", icon = "SCRIPT")
        row.operator("meltdown.clear_setup", icon = "CANCEL")
        
        row = box.row(align=True)
        row.alignment = 'EXPAND'
        row.operator("meltdown.bake", text='Start Baking', icon = "RENDER_STILL")

       
        row = box.row(align=True)
        row.alignment = 'EXPAND'
        
        if setup.material_mode == 'CYCLES':
            row.operator("meltdown.enable_cycles", icon = "FILE_TICK")
        else:
            row.operator("meltdown.enable_cycles", icon = "MATERIAL_DATA")
            
        if setup.material_mode == 'BLENDER_RENDER':
            row.operator("meltdown.enable_bi", icon = "FILE_TICK")
        else:
            row.operator("meltdown.enable_bi", icon = "MATERIAL_DATA")
        
        if setup.material_mode == 'BAKED':
            row.operator("meltdown.enable_baked", icon = "FILE_TICK")
        else:
            row.operator("meltdown.enable_baked", icon = "MATERIAL_DATA")
            
        row.separator()

class MeltdownJobsPanel(bpy.types.Panel):
    bl_label = "Baking jobs"
    bl_idname = "OBJECT_PT_meltdown_job"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "Baking"
    
    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "CYCLES" or context.scene.render.engine == "BLENDER_RENDER"
    
    def draw(self, context):
        layout = self.layout
        edit = context.user_preferences.edit
        wm = context.window_manager
        mds = context.scene.meltdown_settings
        
        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        row.separator()
        
        for job_i, job in enumerate(mds.jobs):
            
            row = layout.row(align=True)
            row.alignment = 'EXPAND'
            
            if job.expand == False: 
                row.prop(job, "expand", icon="TRIA_RIGHT", icon_only=True, text=str(len(job.pairs))+" Objects", emboss=False)
                
                if job.activated:
                    row.prop(job, "activated", icon_only=True, icon = "RESTRICT_RENDER_OFF", emboss = False)
                else:
                    row.prop(job, "activated", icon_only=True, icon = "RESTRICT_RENDER_ON", emboss = False)
                    
                rem = row.operator("meltdown.rem_job", text = "", icon = "X")
                rem.job_index = job_i  
            else:
                row.prop(job, "expand", icon="TRIA_DOWN", icon_only=True, text=str(len(job.pairs))+" Objects", emboss=False)
                
                if job.activated:
                    row.prop(job, "activated", icon_only=True, icon = "RESTRICT_RENDER_OFF", emboss = False)
                else:
                    row.prop(job, "activated", icon_only=True, icon = "RESTRICT_RENDER_ON", emboss = False)

                rem = row.operator("meltdown.rem_job", text = "", icon = "X")
                rem.job_index = job_i            
                
                row = layout.row(align=True)
                row.alignment = 'EXPAND'
                row.prop(job, 'resolution_x', text="X")
                row.prop(job, 'resolution_y', text="Y")
                
                row = layout.row(align=True)
                row.alignment = 'EXPAND'
                row.prop(job, 'antialiasing', text="4x Antialiasing")
                
                
                if job.antialiasing == True:
                    row = layout.row(align=True)
                    row.alignment = 'EXPAND'
                    row.prop(job, 'aa_sharpness', text="AA sharpness")
                
                row = layout.row(align=True)
                row.alignment = 'EXPAND'
                row.prop(job, 'margin', text="Margin")
                
                
                row = layout.row(align=True)
                row.alignment = 'EXPAND'
                row.prop(job, 'output', text="Path")
                
                row = layout.row(align=True)
                row.alignment = 'EXPAND'
                row.prop(job, 'output_format', text="Format")
                
                
                for pair_i, pair in enumerate(job.pairs):
                    row = layout.row(align=True)
                    row.alignment = 'EXPAND'
                    box = row.box().column(align=True)
                    
                    subrow = box.row(align=True)
                    subrow.prop_search(pair, "lowpoly", bpy.context.scene, "objects")
                        
                    subrow = box.row(align=True)
                    subrow.prop(pair, 'hp_obj_vs_group', expand=True)
                    if pair.hp_obj_vs_group == 'OBJ':
                        subrow.prop_search(pair, "highpoly", bpy.context.scene, "objects")
                    else:
                        subrow.prop_search(pair, "highpoly", bpy.data, "groups")
                    subrow = box.row(align=True)
                    
                    subrow.prop(pair, 'extrusion_vs_cage', expand=True)
                    if pair.extrusion_vs_cage == "EXT":
                        subrow.prop(pair, 'extrusion', expand=True)
                    else:
                        subrow.prop_search(pair, "cage", bpy.context.scene, "objects")
                    
                    col = row.column()
                    row = col.row()
                    rem = row.operator("meltdown.rem_pair", text = "", icon = "X")
                    rem.pair_index = pair_i
                    rem.job_index = job_i
                    
                    row = col.row()
                    if pair.activated:
                        row.prop(pair, "activated", icon_only=True, icon = "RESTRICT_RENDER_OFF", emboss = False)
                    else:
                        row.prop(pair, "activated", icon_only=True, icon = "RESTRICT_RENDER_ON", emboss = False)
                        
                row = layout.row(align=True)
                row.alignment = 'EXPAND'
                addpair = row.operator("meltdown.add_pair", icon = "ZOOMIN")
                addpair.job_index = job_i
                
                for pass_i, bakepass in enumerate(job.bakepasses):
                    row = layout.row(align=True)
                    row.alignment = 'EXPAND'
                    box = row.box().column(align=True)
                    bakepass.draw(box)
                      
                row = layout.row(align=True)
                row.alignment = 'EXPAND'
                addpass = row.operator("meltdown.add_pass", icon = "ZOOMIN")
                addpass.job_index = job_i
                
                row = layout.row(align=True)
                row.alignment = 'EXPAND'
                row.separator()
            
        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        row.operator("meltdown.add_job", icon = "ZOOMIN")

def register():
    register_class(BakePair)    
    register_class(BakePass)            
    register_class(BakeJob)
    register_class(SmartUnwrapProps)
    register_class(LightmapUnwrapProps)
    register_class(MeltdownSettings)
    register_class(MeltdownSetup)     
    bpy.types.Scene.meltdown_setup = PointerProperty(type = MeltdownSetup)
    bpy.types.Scene.meltdown_settings = PointerProperty(type = MeltdownSettings)
    bpy.utils.register_module(__name__)
    # use custom props for temporary datas, to clean up the scene when not needed
    #bpy.types.Object.md_orig_name = StringProperty(name="Original Name")
    #bpy.types.Group.md_orig_name = StringProperty(name="Original Name")
    #bpy.types.World.md_orig_name = StringProperty(name="Original Name")
    #bpy.types.Material.md_orig_name = StringProperty(name="Original Name")
    print("Hello World!")
    
def unregister():
    unregister_class(MeltdownSettings)
    unregister_class(MeltdownSetup)
    unregister_class(SmartUnwrapProps)
    unregister_class(LightmapUnwrapProps)
    unregister_class(BakePair)    
    unregister_class(BakePass)            
    unregister_class(BakeJob)
    bpy.utils.unregister_module(__name__)
    del bpy.types.Scene.meltdown_setup
    del bpy.types.Scene.meltdown_settings
    #del bpy.types.Object.md_orig_name
    #del bpy.types.Group.md_orig_name 
    #del bpy.types.World.md_orig_name 
    #del bpy.types.Material.md_orig_name
    print("Goodbye World!")
    

if __name__ == "__main__":
    register()  
