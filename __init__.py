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
    "tracker_url": "https://github.com/MadMinstrel/meltdown/issues",
    "category": "Baking"}

import code
import os
import bpy
from bpy.props import *
from bpy.utils import register_class, unregister_class

class BakePair(bpy.types.PropertyGroup):
    activated = bpy.props.BoolProperty(name = "Activated", description="Pair on/off", default = True)
    lowpoly = bpy.props.StringProperty(name="", description="Lowpoly mesh", default="")
    cage = bpy.props.StringProperty(name="", description="Cage mesh", default="")
    highpoly = bpy.props.StringProperty(name="", description="Highpoly mesh", default="")
    hp_obj_vs_group = EnumProperty(name="Object vs Group", description="", default="OBJ", items = [('OBJ', '', 'Object', 'MESH_CUBE', 0), ('GRP', '', 'Group', 'GROUP', 1)])
    extrusion_vs_cage = EnumProperty(name="Extrusion vs Cage", description="", default="EXT", items = [('EXT', '', 'Extrusion', 'OUTLINER_DATA_META', 0), ('CAGE', '', 'Cage', 'OUTLINER_OB_LATTICE', 1)])
    extrusion = bpy.props.FloatProperty(name="Extrusion", description="", default=0.5, min=0.0)
    use_hipoly = bpy.props.BoolProperty(name="Use Hipoly", default = True)
    no_materials = bpy.props.BoolProperty(name="No Materials", default = False)

def update_pass_name(self, context):
    self.suffix = self.pass_name.lower()
    
class BakePass(bpy.types.PropertyGroup):
    activated = bpy.props.BoolProperty(name = "Activated", default = True)
    pair_counter = bpy.props.IntProperty(name="Pair Counter", description="", default=0)
    pass_name = bpy.props.EnumProperty(name = "Pass", default = "NORMAL",
                                    items = (("COMBINED","Combined",""),
                                            ("MAT_ID","Material ID",""),
                                            #("Z","Depth",""),
                                            #("COLOR","Color",""),
                                            # ("DIFFUSE","Diffuse",""),
                                            #("SPECULAR","Specular",""),
                                            ("SHADOW","Shadow",""),
                                            ("AO","Ambient Occlusion",""),
                                            #("REFLECTION","Reflection",""),
                                            ("NORMAL","Normal",""),
                                            #("VECTOR","Vector",""),
                                            #("REFRACTION","Refraction",""),
                                            #("OBJECT_INDEX","Object Index",""),
                                            ("UV","UV",""),
                                            #("MIST","Mist",""),
                                            ("EMIT","Emission",""),
                                            ("ENVIRONMENT","Environment",""),
                                            #("MATERIAL_INDEX","Material Index",""),
                                            ("DIFFUSE_DIRECT","DIffuse Direct",""),
                                            ("DIFFUSE_INDIRECT","Diffuse Indirect",""),
                                            ("DIFFUSE_COLOR","Diffuse Color",""),
                                            ("GLOSSY_DIRECT","Glossy Direct",""),
                                            ("GLOSSY_INDIRECT","Glossy Indirect",""),
                                            ("GLOSSY_COLOR","Glossy Color",""),
                                            ("TRANSMISSION_DIRECT","Transmission Direct",""),
                                            ("TRANSMISSION_INDIRECT","Transmission Indirect",""),
                                            ("TRANSMISSION_COLOR","Transmission Color",""),
                                            ("SUBSURFACE_DIRECT","Subsurface Direct",""),
                                            ("SUBSURFACE_INDIRECT","Subsurface Indirect",""),
                                            ("SUBSURFACE_COLOR","Subsurface Color","")), 
                                            update=update_pass_name)
    influence = bpy.props.FloatProperty(name="Influence", description="BI texture influence", default=1.0, min=0.0)    
    material_override = bpy.props.StringProperty(name="Material Override", description="", default="")
    ao_distance = bpy.props.FloatProperty(name="Distance", description="", default=10.0, min=0.0)
    samples = bpy.props.IntProperty(name="Samples", description="", default=1)
    suffix = bpy.props.StringProperty(name="Suffix", description="", default="")
    clean_environment = bpy.props.BoolProperty(name = "Clean Environment", default = False)
    environment_highpoly = bpy.props.BoolProperty(name = "Highpoly", default = False)
    environment_group = bpy.props.StringProperty(name="", description="Environment", default="")
    
    nm_space = bpy.props.EnumProperty(name = "Normal map space", default = "TANGENT",
                                    items = (("TANGENT","Tangent",""),
                                            ("OBJECT", "Object", "")))

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
    def props(self):
        props = set()
        if self.pass_name == "COMBINED":
            props = {"samples", "clean_environment", "environment"}
        if self.pass_name == "SHADOW":
            props = {"samples"}
        if self.pass_name == "AO":
            props = {"ao_distance", "samples", "clean_environment", "environment"}
        if self.pass_name == "NORMAL":
            props = {"nm_space", "swizzle"}
        # if self.pass_name == "DIFFUSE":
            # props = {"samples", "clean_environment", "environment"}
        if self.pass_name == "DIFFUSE_DIRECT":
            props = {"samples", "clean_environment", "environment"}
        if self.pass_name == "DIFFUSE_INDIRECT":
            props = {"samples", "clean_environment", "environment"}
        if self.pass_name == "GLOSSY_DIRECT":
            props = {"samples", "clean_environment", "environment"}
        if self.pass_name == "GLOSSY_INDIRECT":
            props = {"samples", "clean_environment", "environment"}
        if self.pass_name == "TRANSMISSION_DIRECT":
            props = {"samples"}
        if self.pass_name == "TRANSMISSION_INDIRECT":
            props = {"samples"}
        if self.pass_name == "SUBSURFACE_DIRECT":
            props = {"samples"}
        if self.pass_name == "SUBSURFACE_INDIRECT":
            props = {"samples"}            
        return props
    

    def get_cycles_pass_type(self):
        # pass_type, pass_filter
        if self.pass_name == "COMBINED": return "COMBINED", {'AO', 'EMIT', 'DIRECT', 'INDIRECT', 'DIFFUSE', 'GLOSSY', 'TRANSMISSION', 'SUBSURFACE'}
        if self.pass_name == "MAT_ID": return "DIFFUSE", {'COLOR'} 
        if self.pass_name == "SHADOW": return "SHADOW", {'NONE'}
        if self.pass_name == "AO": return "AO", {'NONE'}
        if self.pass_name == "NORMAL": return "NORMAL", {'NONE'}
        if self.pass_name == "UV": return "UV", {'NONE'}
        if self.pass_name == "EMIT": return "EMIT", {'NONE'}
        if self.pass_name == "ENVIRONMENT": return "ENVIRONMENT", {'NONE'}
        if self.pass_name == "DIFFUSE_DIRECT": return "DIFFUSE", {'DIRECT'}
        if self.pass_name == "DIFFUSE_INDIRECT": return "DIFFUSE", {'INDIRECT'}
        if self.pass_name == "DIFFUSE_COLOR": return "DIFFUSE", {'COLOR'}
        if self.pass_name == "GLOSSY_DIRECT": return "GLOSSY", {'DIRECT'}
        if self.pass_name == "GLOSSY_INDIRECT": return "GLOSSY", {'INDIRECT'}
        if self.pass_name == "GLOSSY_COLOR": return "GLOSSY", {'COLOR'}
        if self.pass_name == "TRANSMISSION_DIRECT": return "TRANSMISSION",  {'DIRECT'}
        if self.pass_name == "TRANSMISSION_INDIRECT": return "TRANSMISSION",  {'INDIRECT'}
        if self.pass_name == "TRANSMISSION_COLOR": return "TRANSMISSION",  {'COLOR'}
        if self.pass_name == "SUBSURFACE_DIRECT": return "SUBSURFACE",  {'DIRECT'}
        if self.pass_name == "SUBSURFACE_INDIRECT": return "SUBSURFACE",  {'INDIRECT'}
        if self.pass_name == "SUBSURFACE_COLOR": return "SUBSURFACE",  {'COLOR'}
    
    def get_blend_mode(self):
        if "COLOR" in self.pass_name or self.pass_name in ["SHADOW","AO"]:
            return 'MULTIPLY'
        if "DIRECT" in self.pass_name:
            return 'ADD'
        return 'MIX'
           
    def get_filepath(self, bj):
        path = bj.output 
        if path[-1:] != "/":
            path = path + "/"
        path = path + bj.name 
        if len(self.suffix)>0:
            path += "_" + self.suffix
        path += ".png"
        return path

    def get_filename(self, bj):
        name = bj.name 
        if len(self.suffix)>0:
            name += "_" + self.suffix
        name += ".png"
        return name        
  
class BakeJob(bpy.types.PropertyGroup):
    activated = bpy.props.BoolProperty(name = "Activated", default = True)
    expand = bpy.props.BoolProperty(name = "Expand", default = True)
    resolution_x = bpy.props.IntProperty(name="Resolution X", default = 1024)
    resolution_y = bpy.props.IntProperty(name="Resolution Y", default = 1024)
    antialiasing = bpy.props.BoolProperty(name="4x Antialiasing", description="", default=False)
    aa_sharpness = bpy.props.FloatProperty(name="AA Sharpness", description="", default=0.5, min = 0.0, max = 1.0)
    
    margin = bpy.props.IntProperty(name="Margin", default = 16, min = 0)
    
    output = bpy.props.StringProperty(name = 'File path',
                            description = 'The path of the output image.',
                            default = '//textures/',
                            subtype = 'FILE_PATH')
    name = bpy.props.StringProperty(name = 'name',
                            description = '',
                            default = 'bake')
    
    bake_queue = bpy.props.CollectionProperty(type=BakePair)
    bake_pass_queue = bpy.props.CollectionProperty(type=BakePass)
    
    def get_render_resolution(self):
        if self.antialiasing == True:
            return [self.resolution_x * 2, self.resolution_y * 2]
        else:
            return [self.resolution_x, self.resolution_y]

class MeltdownSettings(bpy.types.PropertyGroup):
    bl_idname = __name__
    bake_job_queue = bpy.props.CollectionProperty(type=BakeJob)

class MeltdownBakeOp(bpy.types.Operator):
    '''Process baking jobs'''

    bl_idname = "meltdown.bake"
    bl_label = "Start Baking"
    
    job = bpy.props.IntProperty()
    bakepass = bpy.props.IntProperty()
    pair = bpy.props.IntProperty()
    bake_all = bpy.props.BoolProperty()
    bake_target = bpy.props.StringProperty()
    
    def create_temp_node(self):
        mds = bpy.context.scene.meltdown_settings
        pair = mds.bake_job_queue[self.job].bake_queue[self.pair]
        imgnode = None
        #add an image node to the lowpoly model's materials
        for bake_mat in bpy.data.scenes["MD_TEMP"].objects[pair.lowpoly+"_MD_TMP"].data.materials:
        
            #bake_mat = bpy.data.scenes["MD_TEMP"].objects[pair.lowpoly+"_MD_TMP"].active_material
        
            bake_mat.use_nodes = True
            if "MDtarget" not in bake_mat.node_tree.nodes:
                imgnode = bake_mat.node_tree.nodes.new(type = "ShaderNodeTexImage")
                imgnode.image = bpy.data.images["MDtarget"]
                imgnode.name = 'MDtarget'
                imgnode.label = 'MDtarget'
            else:
                imgnode = bake_mat.node_tree.nodes['MDtarget']
                imgnode.image = bpy.data.images["MDtarget"]
            
            bake_mat.node_tree.nodes.active = imgnode
        
        if imgnode is not None:
            bake_mat = bpy.data.scenes["MD_TEMP"].objects[pair.lowpoly+"_MD_TMP"].active_material
            bake_mat.node_tree.nodes.active = imgnode
        
    def create_render_target(self):
        mds = bpy.context.scene.meltdown_settings
        job = mds.bake_job_queue[self.job]

        bpy.ops.image.new(name="MDtarget", width= job.get_render_resolution()[0], \
        height = job.get_render_resolution()[1], \
        color=(0.0, 0.0, 0.0, 0.0), alpha=True, generated_type='BLANK', float=False)
        
    def cleanup_render_target(self):
        baketarget = bpy.data.images["MDtarget"]
        
        # call compo trees here
        self.compo_nodes_margin(baketarget)
        
        #unlink from image editors
        for wm in bpy.data.window_managers:
            for window in wm.windows:
                for area in window.screen.areas:
                    if area.type == "IMAGE_EDITOR":
                        area.spaces[0].image = None
    
    # def apply_modifiers(self):
    
    # def merge_group(self):
    
    def scene_copy(self):
        # store the original names of things in the scene so we can easily identify them later
        for object in bpy.context.scene.objects:
            object.md_orig_name = object.name
        for group in bpy.data.groups:
            group.md_orig_name = group.name
        for world in bpy.data.worlds:
            world.md_orig_name = world.name
        for material in bpy.data.materials:
            material.md_orig_name = material.name
        
        # duplicate the scene
        bpy.ops.scene.new(type='FULL_COPY')
        bpy.context.scene.name = "MD_TEMP"
        
        # tag the copied object names with _MD_TMP
        for object in bpy.data.scenes["MD_TEMP"].objects:
            object.name = object.md_orig_name + "_MD_TMP"
        for group in bpy.data.groups:
            if group.name != group.md_orig_name:
                group.name = group.md_orig_name + "_MD_TMP"
        for world in bpy.data.worlds:
            if world.name != world.md_orig_name:
                world.name = "MD_TEMP"
        for material in bpy.data.materials:
            if material.name != material.md_orig_name:
                material.name = material.md_orig_name + "_MD_TMP"
    
    def scene_new_compo(self):
        bpy.ops.scene.new(type = "EMPTY")
        bpy.context.scene.name = "MD_COMPO"
    
    def copy_cycles_settings(self):
        mds = bpy.context.scene.meltdown_settings
        bakepass = mds.bake_job_queue[self.job].bake_pass_queue[self.bakepass]
        cycles = bpy.data.scenes["MD_TEMP"].cycles
        #copy pass settings to cycles settings
        bake_type, pass_filter = bakepass.get_cycles_pass_type()
        bpy.data.scenes["MD_TEMP"].cycles.bake_type = bake_type
        bpy.data.scenes["MD_TEMP"].cycles.samples = bakepass.samples
        bpy.data.worlds["MD_TEMP"].light_settings.distance = bakepass.ao_distance
    
    def pass_material_id_prep(self):
        mds = bpy.context.scene.meltdown_settings
        pair = mds.bake_job_queue[self.job].bake_queue[self.pair]
        
        def change_material(hp):
            for slot in hp.material_slots:
                mat = slot.material
                mat.use_nodes = True
                
                for node in mat.node_tree.nodes:
                    mat.node_tree.nodes.remove(node)
                
                tree = mat.node_tree
                
                tree.nodes.new(type = "ShaderNodeBsdfDiffuse")
                tree.nodes.new(type = "ShaderNodeOutputMaterial")
                output = tree.nodes["Diffuse BSDF"].outputs["BSDF"]
                input = tree.nodes["Material Output"].inputs["Surface"]
                tree.links.new(output, input)
                
                mat.node_tree.nodes["Diffuse BSDF"].inputs["Color"].default_value = \
                [mat.diffuse_color[0], mat.diffuse_color[1], mat.diffuse_color[2], 1]
        
        
        if pair.highpoly != "":
            if pair.hp_obj_vs_group == "GRP":
                for object in bpy.data.groups[pair.highpoly+"_MD_TMP"].objects:
                    change_material(object)
            else:
                change_material(hp = bpy.data.scenes["MD_TEMP"].objects[pair.highpoly+"_MD_TMP"])
        
    
    def prepare_scene(self):
        mds = bpy.context.scene.meltdown_settings
        pair = mds.bake_job_queue[self.job].bake_queue[self.pair]
        pair_list = mds.bake_job_queue[self.job].bake_queue
        bakepass = mds.bake_job_queue[self.job].bake_pass_queue[self.bakepass]
        
        self.scene_copy()
        self.copy_cycles_settings()
        
        # bpy.data.scenes["MD_TEMP"].active_layer = 0
        bpy.data.scenes["MD_TEMP"].layers[0] = True
        
        # make selections, ensure visibility
        bpy.ops.object.select_all(action='DESELECT')
        if pair.highpoly != "":
            if pair.hp_obj_vs_group == "GRP":
                for object in bpy.data.groups[pair.highpoly+"_MD_TMP"].objects:
                    object.hide = False
                    object.hide_select = False
                    object.hide_render = False
                    object.layers[0] = True
                    object.select = True
            else:
                bpy.data.scenes["MD_TEMP"].objects[pair.highpoly+"_MD_TMP"].hide = False
                bpy.data.scenes["MD_TEMP"].objects[pair.highpoly+"_MD_TMP"].hide_select = False
                bpy.data.scenes["MD_TEMP"].objects[pair.highpoly+"_MD_TMP"].hide_render = False
                bpy.data.scenes["MD_TEMP"].objects[pair.highpoly+"_MD_TMP"].layers[0] = True
                bpy.data.scenes["MD_TEMP"].objects[pair.highpoly+"_MD_TMP"].select = True
        else:
            pair.use_hipoly = False
        
        #lowpoly visibility
        bpy.data.scenes["MD_TEMP"].objects[pair.lowpoly+"_MD_TMP"].hide = False
        bpy.data.scenes["MD_TEMP"].objects[pair.lowpoly+"_MD_TMP"].hide_select = False
        bpy.data.scenes["MD_TEMP"].objects[pair.lowpoly+"_MD_TMP"].hide_render = False
        bpy.data.scenes["MD_TEMP"].objects[pair.lowpoly+"_MD_TMP"].layers[0] = True
        bpy.data.scenes["MD_TEMP"].objects[pair.lowpoly+"_MD_TMP"].select = True
        
        #cage visibility
        if pair.cage != "":
            bpy.data.scenes["MD_TEMP"].objects[pair.cage+"_MD_TMP"].hide = True
            bpy.data.scenes["MD_TEMP"].objects[pair.cage+"_MD_TMP"].hide_render = True
        
        bpy.context.scene.objects.active = bpy.data.scenes["MD_TEMP"].objects[pair.lowpoly+"_MD_TMP"]
        
        if bakepass.clean_environment == False and bakepass.environment_highpoly == True:
            # iterate over objects designated as highpoly and select them
            for rem_i, rem_pair in enumerate(pair_list):
                if rem_pair.hp_obj_vs_group == "GRP":
                    for object in  bpy.data.groups[rem_pair.highpoly+"_MD_TMP"].objects:
                        object.hide = False
                        object.hide_select = False
                        object.hide_render = False
                        object.select = True
                        object.layers[0] = True
                else:
                    bpy.data.scenes["MD_TEMP"].objects[pair.highpoly+"_MD_TMP"].hide = False
                    bpy.data.scenes["MD_TEMP"].objects[pair.highpoly+"_MD_TMP"].hide_select = False
                    bpy.data.scenes["MD_TEMP"].objects[pair.highpoly+"_MD_TMP"].hide_render = False
                    bpy.data.scenes["MD_TEMP"].objects[rem_pair.highpoly+"_MD_TMP"].select = True
                    bpy.data.scenes["MD_TEMP"].objects[rem_pair.highpoly+"_MD_TMP"].layers[0] = True
                
        if bakepass.clean_environment == False \
        and bakepass.environment_highpoly == False \
        and bakepass.environment_group != "":
            for object in bpy.data.groups[bakepass.environment_group+"_MD_TMP"].objects:
                object.hide = False
                object.hide_select = False
                object.hide_render = False
                object.select = True
                object.layers[0] = True
        
        # remove unnecessary objects
        if bakepass.environment_group != "" \
        or bakepass.clean_environment == True \
        or bakepass.environment_highpoly == True: #do not remove if environment group empty
            for object in bpy.data.scenes["MD_TEMP"].objects:
                if object.select == False:
                    self.remove_object(object)
        
        if bakepass.pass_name == "MAT_ID":
            self.pass_material_id_prep()
        
    def bake_set(self):
        mds = bpy.context.scene.meltdown_settings
        pair = mds.bake_job_queue[self.job].bake_queue[self.pair]
        bakepass = mds.bake_job_queue[self.job].bake_pass_queue[self.bakepass]
        bj = mds.bake_job_queue[self.job]
        
        self.prepare_scene()
        
        no_materials = False
        #ensure lowpoly has material
        if len(bpy.data.scenes["MD_TEMP"].objects[pair.lowpoly+"_MD_TMP"].data.materials) == 0 \
            or bpy.data.scenes["MD_TEMP"].objects[pair.lowpoly+"_MD_TMP"].material_slots[0].material == None:
            no_materials = True
            temp_mat = bpy.data.materials.new("Meltdown_MD_TMP")
            temp_mat.use_nodes = True
            bpy.data.scenes["MD_TEMP"].objects[pair.lowpoly+"_MD_TMP"].data.materials.append(temp_mat)
            bpy.data.scenes["MD_TEMP"].objects[pair.lowpoly+"_MD_TMP"].active_material = temp_mat
        
        self.create_temp_node()
        
        if pair.extrusion_vs_cage == "CAGE":
            pair_use_cage = True
        else:
            pair_use_cage = False
        
        clear = True
        if bakepass.pair_counter > 0:
            clear = False
        bakepass.pair_counter = bakepass.pair_counter + 1
        
        #bake
        bake_type, pass_filter = bakepass.get_cycles_pass_type()
        bpy.ops.object.bake(type=bpy.context.scene.cycles.bake_type, pass_filter=pass_filter, \
        filepath="", \
        width=bj.get_render_resolution()[0], height=bj.get_render_resolution()[1], margin=0, \
        use_selected_to_active=pair.use_hipoly, cage_extrusion=pair.extrusion, cage_object=pair.cage, \
        normal_space=bakepass.nm_space, \
        normal_r=bakepass.normal_r, normal_g=bakepass.normal_g, normal_b=bakepass.normal_b, \
        save_mode='INTERNAL', use_clear=clear, use_cage=pair_use_cage, \
        use_split_materials=False, use_automatic_name=False)
    
        self.cleanup()
          
    def bake_pass(self):
        mds = bpy.context.scene.meltdown_settings
        bakepass = mds.bake_job_queue[self.job].bake_pass_queue[self.bakepass]
        bj = mds.bake_job_queue[self.job]

        #the pair counter is used to determine whether to clear the image
        #set it to 0 after each bake pass
        bakepass.pair_counter = 0
        
        for i_pair, pair in enumerate(bj.bake_queue):
            if pair.activated == True:
                self.pair = i_pair
                self.bake_set()
    
        self.cleanup_render_target()

    def remove_object(self, object):
        if bpy.data.objects[object.name]:            
            if object.type == "MESH":
                bpy.data.scenes["MD_TEMP"].objects.unlink(object)
                mesh_to_remove = object.data
                bpy.data.objects.remove(object)
                bpy.data.meshes.remove(mesh_to_remove)
            else:
                bpy.data.scenes["MD_TEMP"].objects.unlink(object)
                bpy.data.objects.remove(object)
    
    def cleanup(self):
        
        for object in bpy.data.scenes["MD_TEMP"].objects:
            self.remove_object(object)
        
        for material in bpy.data.materials:
            if material.name.endswith("_MD_TMP"):
                bpy.data.materials.remove(material)
        
        for group in bpy.data.groups:
            if group.name.endswith("_MD_TMP"):
                bpy.data.groups.remove(group)
        
        bpy.ops.scene.delete()
    
    def compo_nodes_margin(self, targetimage):
        mds = bpy.context.scene.meltdown_settings
        bj = mds.bake_job_queue[self.job]
        bakepass = mds.bake_job_queue[self.job].bake_pass_queue[self.bakepass]
        # job = mds.bake_job_queue[self.job]
        self.scene_new_compo()
        
        # make sure the compositor is using nodes
        bpy.data.scenes["MD_COMPO"].use_nodes = True
        bpy.data.scenes["MD_COMPO"].render.resolution_x = bj.resolution_x
        bpy.data.scenes["MD_COMPO"].render.resolution_y = bj.resolution_y
        bpy.data.scenes["MD_COMPO"].render.resolution_percentage = 100
        bpy.data.scenes["MD_COMPO"].render.filepath = bakepass.get_filepath(bj)
        bpy.data.scenes["MD_COMPO"].render.image_settings.compression = 0
        
        tree = bpy.data.scenes["MD_COMPO"].node_tree
        
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

        if bj.antialiasing == True:
            margin = bj.margin*2
            filter_width = (1.0-bj.aa_sharpness)/2.0
            print("filter "+str(filter_width))
            transform_scale = 0.5
        else:
            margin = bj.margin
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
        mds = context.scene.meltdown_settings
        self.create_render_target()
        for i_job, bj in enumerate(mds.bake_job_queue):
            if bj.activated == True:
                self.job = i_job
                
                # ensure save path exists
                if not os.path.exists(bpy.path.abspath(bj.output)):
                    os.makedirs(bpy.path.abspath(bj.output))
                
                for i_pass, bakepass in enumerate(bj.bake_pass_queue):
                    if bakepass.activated == True:
                        self.bakepass = i_pass
                        self.bake_pass()
        
        bpy.data.images["MDtarget"].user_clear()
        bpy.data.images.remove(bpy.data.images["MDtarget"])
        
        return {'FINISHED'}

class MeltdownAddPairOp(bpy.types.Operator):
    '''add pair'''

    bl_idname = "meltdown.add_pair"
    bl_label = "Add Pair"
    
    job_index = bpy.props.IntProperty()
    def execute(self, context):
        scene_name = bpy.context.scene.name
        bpy.data.scenes[scene_name].meltdown_settings.bake_job_queue[self.job_index].bake_queue.add()
        
        return {'FINISHED'}

class MeltdownRemPairOp(bpy.types.Operator):
    '''delete pair'''

    bl_idname = "meltdown.rem_pair"
    bl_label = "Remove Pair"
    
    pair_index = bpy.props.IntProperty()
    job_index = bpy.props.IntProperty()
    def execute(self, context):
        scene_name = bpy.context.scene.name
        bpy.data.scenes[scene_name].meltdown_settings.bake_job_queue[self.job_index].bake_queue.remove(self.pair_index)
        
        return {'FINISHED'}
        
class MeltdownAddPassOp(bpy.types.Operator):
    '''add pass'''

    bl_idname = "meltdown.add_pass"
    bl_label = "Add Pass"
    
    job_index = bpy.props.IntProperty()
    def execute(self, context):
        scene_name = bpy.context.scene.name
        bpy.data.scenes[scene_name].meltdown_settings.bake_job_queue[self.job_index].bake_pass_queue.add()
        return {'FINISHED'}

class MeltdownRemPassOp(bpy.types.Operator):
    '''delete pass'''

    bl_idname = "meltdown.rem_pass"
    bl_label = "Remove Pass"
    
    pass_index = bpy.props.IntProperty()
    job_index = bpy.props.IntProperty()
    def execute(self, context):
        scene_name = bpy.context.scene.name
        bpy.data.scenes[scene_name].meltdown_settings.bake_job_queue[self.job_index].bake_pass_queue.remove(self.pass_index)
        return {'FINISHED'}

class MeltdownAddJobOp(bpy.types.Operator):
    '''add job'''

    bl_idname = "meltdown.add_job"
    bl_label = "Add Bake Job"
    
    def execute(self, context):
        scene_name = bpy.context.scene.name
        bpy.data.scenes[scene_name].meltdown_settings.bake_job_queue.add()
        return {'FINISHED'}

class MeltdownRemJobOp(bpy.types.Operator):
    '''delete job'''

    bl_idname = "meltdown.rem_job"
    bl_label = "Remove Bake Job"
    
    job_index = bpy.props.IntProperty()
    def execute(self, context):
        scene_name = bpy.context.scene.name
        bpy.data.scenes[scene_name].meltdown_settings.bake_job_queue.remove(self.job_index)
        return {'FINISHED'}

class MeltdownUnwrap(bpy.types.Operator):
    '''unwrap'''

    bl_idname = "meltdown.unwrap"
    bl_label = "Unwrap"
    def execute(self, context):
        wm = context.window_manager
        scene = context.scene
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
            bpy.ops.uv.unwrap()
            self.report({'INFO'}, "Reset UVS using your marked seams.")
        else: 
            bpy.ops.uv.smart_project(island_margin = 0.02, angle_limit = 45)
            self.report({'INFO'}, "Reset UVS using Smart UV Project.")
        bpy.ops.object.mode_set(mode='OBJECT')
        return {'FINISHED'}

class MeltdownMakeSetupPassOp(bpy.types.Operator):
    '''Setup pass jobs for selection'''

    bl_idname = "meltdown.add_setup"
    bl_label = "Setup jobs"
    
    def execute(self, context):
        scene_name = context.scene.name
        objs = [obj for obj in context.selected_objects if obj.type == 'MESH']
        settings = bpy.data.scenes[scene_name].meltdown_setup
        meltdown_settings = bpy.data.scenes[scene_name].meltdown_settings
        meltdown_settings.bake_job_queue.clear()
        for i, obj in enumerate(objs):
            if not obj.data.uv_textures:
                context.scene.objects.active = obj
                bpy.ops.meltdown.unwrap()
            job = meltdown_settings.bake_job_queue.add()
            job.name = obj.name
            job.expand = False
            job.output = settings.output
            job.antialiasing = settings.antialiasing
            job.resolution_x = settings.resolution_x
            job.resolution_y = settings.resolution_y  
            pair = job.bake_queue.add()
            pair.lowpoly = obj.name
            for j, bake_pass in enumerate(settings.bake_pass_queue):
                new_bake_pass = job.bake_pass_queue.add()
                new_bake_pass.pass_name = bake_pass.pass_name
                new_bake_pass.activated = bake_pass.activated
                new_bake_pass.suffix = bake_pass.suffix
                new_bake_pass.samples = bake_pass.samples
                new_bake_pass.clean_environment = bake_pass.clean_environment
                new_bake_pass.ao_distance = bake_pass.ao_distance
                new_bake_pass.material_override = bake_pass.material_override
                new_bake_pass.environment_highpoly = bake_pass.environment_highpoly
                new_bake_pass.environment_group = bake_pass.environment_group
                new_bake_pass.nm_space = bake_pass.nm_space
                new_bake_pass.normal_r = bake_pass.normal_r
                new_bake_pass.normal_g = bake_pass.normal_g
                new_bake_pass.normal_b = bake_pass.normal_b
        bpy.ops.meltdown.enable_cycles()
        return {'FINISHED'}


class MeltdownEnableCyclesMaterialOp(bpy.types.Operator):
    '''Show Cycles materials'''

    bl_idname = "meltdown.enable_cycles"
    bl_label = "Enable Cycles"
    
    def execute(self, context):
        scene_name = context.scene.name
        context.scene.render.engine = 'CYCLES'
        settings = bpy.data.scenes[scene_name].meltdown_settings
        for i, job in enumerate(settings.bake_job_queue):
            pair = job.bake_queue[0]
            for j, pass_q in enumerate(job.bake_pass_queue):
                mat = bpy.data.objects[pair.lowpoly].data.materials[0]
                if mat is not None:
                    mat.use_nodes = True
                
        return {'FINISHED'}
        
class MeltdownEnableBiMaterialOp(bpy.types.Operator):
    '''Show bi materials'''

    bl_idname = "meltdown.enable_bi"
    bl_label = "Enable BI"
    
    def execute(self, context):
        scene_name = context.scene.name
        context.scene.render.engine = 'BLENDER_RENDER'
        settings = bpy.data.scenes[scene_name].meltdown_settings
        for i, job in enumerate(settings.bake_job_queue):
            pair = job.bake_queue[0]
            for j, pass_q in enumerate(job.bake_pass_queue):
                mat = bpy.data.objects[pair.lowpoly].data.materials[0]
                if mat is not None:
                    mat.use_nodes = False
                
        return {'FINISHED'}    

class MeltdownMakeBIMaterialOp(bpy.types.Operator):
    '''Setup rendered images in Blender Internal maps'''

    bl_idname = "meltdown.apply_bi"
    bl_label = "Use rendered maps in BI"
    def execute(self, context):
        scene_name = context.scene.name
        settings = bpy.data.scenes[scene_name].meltdown_settings
        for i, job in enumerate(settings.bake_job_queue):
            pair = job.bake_queue[0]
            mat = bpy.data.objects[pair.lowpoly].data.materials[0]
            if mat is not None:
                mat.diffuse_color = (0,0,0)
                mat.use_shadeless = True
                for i, slot in enumerate(mat.texture_slots):
                    if slot is not None:
                        mat.texture_slots.clear(i)
            bake_pass_queue = self.sort_bake_passes(job.bake_pass_queue)
            for j, bake_pass in enumerate(bake_pass_queue):
                if mat is not None:
                    slot = self.find_empty_slot(mat)
                    filename = bake_pass.get_filename(job)
                    filepath = bake_pass.get_filepath(job)
                    tex = bpy.data.textures.new(name=filename, type='IMAGE')
                    img_idx = bpy.data.images.find(filename)
                    if img_idx > -1:
                        image = bpy.data.images[img_idx]
                    else:
                        image = bpy.data.images.load(filepath)
                    tex.image = image
                    self.config_texture_slot(bake_pass, slot)
                    slot.texture = tex
                
        return {'FINISHED'}
    
    def find_empty_slot(self, mat):
        for slot in mat.texture_slots:
            if slot is None:
                return mat.texture_slots.add()
            else:
                if slot.texture is None:
                    return slot
        return mat.texture_slots.add()
     
    def config_texture_slot(self, bake_pass, slot):
    
        slot.blend_type = bake_pass.get_blend_mode()
        
        if 'DIFFUSE' in bake_pass.pass_name or bake_pass.pass_name in ['COMBINED','SHADOW','AO']:
            slot.use_map_color_diffuse = True
            slot.diffuse_color_factor = bake_pass.influence
        else:
            slot.use_map_color_diffuse = False
            
        if 'EMIT' in bake_pass.pass_name:  
            slot.use_map_emit = True
            slot.emit_factor = bake_pass.influence
            
        if 'GLOSSY' in bake_pass.pass_name:
            slot.use_map_color_spec = True
            slot.specular_color_factor = bake_pass.influence
        
        if 'NORMAL' in bake_pass.pass_name:
            slot.use_map_normal = True
            slot.normal_factor = bake_pass.influence

    def get_pass_order(self, item):
        return [ "COMBINED", \
          "DIFFUSE_INDIRECT", "DIFFUSE_DIRECT", "DIFFUSE_COLOR", \
          "GLOSSY_DIRECT", "GLOSSY_INDIRECT", "GLOSSY_COLOR",  \
          "TRANSMISSION_DIRECT", "TRANSMISSION_INDIRECT", "TRANSMISSION_COLOR", \
          "SUBSURFACE_DIRECT", "SUBSURFACE_INDIRECT", "SUBSURFACE_COLOR", \
          "ENVIRONMENT", "EMIT",  "AO", "SHADOW", "NORMAL", "UV", "MAT_ID" \
          ].index(item.pass_name)
          
    def sort_bake_passes(self, bake_pass_queue):
        return sorted(bake_pass_queue, key=self.get_pass_order)

class MeltdownSetup(bpy.types.PropertyGroup):
    bl_idname = 'meltdown.setup_properties'
    expand = bpy.props.BoolProperty(name = "Expand", default = True)
    resolution_x = bpy.props.IntProperty(name="Resolution X", default = 1024)
    resolution_y = bpy.props.IntProperty(name="Resolution Y", default = 1024)
    antialiasing = bpy.props.BoolProperty(name="4x Antialiasing", description="", default=False)
    aa_sharpness = bpy.props.FloatProperty(name="AA Sharpness", description="", default=0.5, min = 0.0, max = 1.0)
    
    margin = bpy.props.IntProperty(name="Margin", default = 16, min = 0)
    
    output = bpy.props.StringProperty(name = 'File path',
                            description = 'The path of the output image.',
                            default = '//textures/',
                            subtype = 'FILE_PATH')
    bake_pass_queue = bpy.props.CollectionProperty(type=BakePass)

class MeltdownAddSetupPassOp(bpy.types.Operator):
    '''add pass'''

    bl_idname = "meltdown.add_setup_pass"
    bl_label = "Add Pass"
    
    def execute(self, context):
        scene_name = bpy.context.scene.name
        bpy.data.scenes[scene_name].meltdown_setup.bake_pass_queue.add()
        return {'FINISHED'}
        
class MeltdownRemSetupPassOp(bpy.types.Operator):
    '''delete pass'''

    bl_idname = "meltdown.rem_setup_pass"
    bl_label = "Remove Pass"
    
    pass_index = bpy.props.IntProperty()
    def execute(self, context):
        scene_name = bpy.context.scene.name
        bpy.data.scenes[scene_name].meltdown_setup.bake_pass_queue.remove(self.pass_index)
        return {'FINISHED'}
        
class MeltdownSetupPanel(bpy.types.Panel):
    bl_label = "Baking setup"
    bl_idname = "OBJECT_PT_meltdown_setup"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "Baking"    
    def draw(self, context):
        layout = self.layout
        edit = context.user_preferences.edit
        wm = context.window_manager
        bj = context.scene.meltdown_setup
        box = layout.box()
        row = box.row(align=True)
        row.label(text="Resolution")
        row = box.row(align=True)
        row.alignment = 'EXPAND'
        row.prop(bj, 'resolution_x', text="X")
        row.prop(bj, 'resolution_y', text="Y")      
        row = box.row(align=True)
        row.alignment = 'EXPAND'
        row.prop(bj, 'antialiasing', text="4x Antialiasing")
        if bj.antialiasing == True:
            row = box.row(align=True)
            row.alignment = 'EXPAND'
            row.prop(bj, 'aa_sharpness', text="AA sharpness")
        row = box.row(align=True)
        row.alignment = 'EXPAND'
        row.prop(bj, 'margin', text="Margin")
        row = box.row(align=True)
        row.alignment = 'EXPAND'
        row.prop(bj, 'output', text="Path")
        
        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        if bj.expand == False: 
            row.prop(bj, "expand", icon="TRIA_RIGHT", icon_only=True, text="Passes", emboss=False)
            for pass_i, bakepass in enumerate(bj.bake_pass_queue):
                row = layout.row(align=True)
                row.alignment = 'EXPAND'
                col = row.column()
                col.prop(bakepass, 'pass_name')
                col = row.column()
                rem = col.operator("meltdown.rem_setup_pass", text = "", icon = "X")
                rem.pass_index = pass_i
                col = row.column()
                if bakepass.activated:
                    col.prop(bakepass, "activated", icon_only=True, icon = "RESTRICT_RENDER_OFF", emboss = False)
                else:
                    col.prop(bakepass, "activated", icon_only=True, icon = "RESTRICT_RENDER_ON", emboss = False)

        else:
            row.prop(bj, "expand", icon="TRIA_DOWN", icon_only=True, text="Passes", emboss=False)
                
            for pass_i, bakepass in enumerate(bj.bake_pass_queue):
                row = layout.row(align=True)
                row.alignment = 'EXPAND'
                box = row.box().column(align=True)
                
                # box = layout.box().column(align=True)
                
                subrow = box.row(align=True)
                subrow.alignment = 'EXPAND'
                subrow.prop(bakepass, 'pass_name')
                box.separator()

                subrow = box.row(align=True)
                subrow.alignment = 'EXPAND'
                subrow.prop(bakepass, 'influence', text="Texture influence")
                #subrow = box.row(align=True)
                #subrow.alignment = 'EXPAND'
                #subrow.prop(bakepass, 'suffix')
                
                if len(bakepass.props())>0:
                    subrow = box.row(align=True)
                    subrow.alignment = 'EXPAND'
                    
                    if "ao_distance" in bakepass.props():
                        subrow = box.row(align=True)
                        subrow.alignment = 'EXPAND'
                        subrow.prop(bakepass, 'ao_distance', text = "AO Distance")
                        
                    if "nm_space" in bakepass.props():
                        box.separator()
                        subrow = box.row(align=True)
                        subrow.alignment = 'EXPAND'
                        subrow.prop(bakepass, 'nm_space', text = "type")

                    if "swizzle" in bakepass.props():
                        box.separator()
                        subrow = box.row(align=True)
                        subrow.alignment = 'EXPAND'
                        subrow.label(text="Swizzle")
                        subrow.prop(bakepass, 'normal_r', text = "")
                        subrow.prop(bakepass, 'normal_g', text = "")
                        subrow.prop(bakepass, 'normal_b', text = "")
                        
                    if "samples" in bakepass.props():
                        subrow = box.row(align=True)
                        subrow.alignment = 'EXPAND'
                        subrow.prop(bakepass, 'samples', text = "Samples")    
                    
                    if "clean_environment" in bakepass.props():
                        subrow = box.row(align=True)
                        subrow.alignment = 'EXPAND'
                        subrow.prop(bakepass, 'clean_environment', text = "Clean Environment")
                    
                    if bakepass.clean_environment == False and "clean_environment" in bakepass.props():
                        subrow = box.row(align=True)
                        subrow.alignment = 'EXPAND'
                        subrow.prop(bakepass, 'environment_highpoly', text = "All Highpoly")  
                    
                    if bakepass.clean_environment == False and \
                    bakepass.environment_highpoly == False and \
                    "clean_environment" in bakepass.props():
                        subrow = box.row(align=True)
                        subrow.alignment = 'EXPAND'
                        subrow.prop_search(bakepass, "environment_group", bpy.data, "groups", text = "Environment")
                        
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
        
        row = box.row(align=True)
        row.alignment = 'EXPAND'
        row.operator("meltdown.bake", text='Start Baking', icon = "RENDER_STILL")

        row = box.row(align=True)
        row.alignment = 'EXPAND'        
        row.operator("meltdown.apply_bi", icon = "IMASEL")
        
        row = box.row(align=True)
        row.alignment = 'EXPAND'
        
        if context.scene.render.engine == 'CYCLES':
            row.operator("meltdown.enable_cycles", icon = "FILE_TICK")
        else:
            row.operator("meltdown.enable_cycles", icon = "SCENE")
            
        if context.scene.render.engine == 'BLENDER_RENDER':
            row.operator("meltdown.enable_bi", icon = "FILE_TICK")
        else:
            row.operator("meltdown.enable_bi", icon = "SCENE")
        
        row.separator()

class MeltdownJobsPanel(bpy.types.Panel):
    bl_label = "Baking jobs"
    bl_idname = "OBJECT_PT_meltdown_job"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "Baking"
    
    @classmethod
    def poll(cls, context):
        return bpy.context.scene.render.engine == "CYCLES"
    
    def draw(self, context):
        layout = self.layout
        edit = context.user_preferences.edit
        wm = context.window_manager
        mds = context.scene.meltdown_settings
        
        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        row.separator()
        
        for job_i, bj in enumerate(mds.bake_job_queue):
            
            row = layout.row(align=True)
            row.alignment = 'EXPAND'
            
            if bj.expand == False: 
                row.prop(bj, "expand", icon="TRIA_RIGHT", icon_only=True, text=bj.name, emboss=False)
                
                if bj.activated:
                    row.prop(bj, "activated", icon_only=True, icon = "RESTRICT_RENDER_OFF", emboss = False)
                else:
                    row.prop(bj, "activated", icon_only=True, icon = "RESTRICT_RENDER_ON", emboss = False)
                    
                rem = row.operator("meltdown.rem_job", text = "", icon = "X")
                rem.job_index = job_i  
            else:
                row.prop(bj, "expand", icon="TRIA_DOWN", icon_only=True, text=bj.name, emboss=False)
                
                if bj.activated:
                    row.prop(bj, "activated", icon_only=True, icon = "RESTRICT_RENDER_OFF", emboss = False)
                else:
                    row.prop(bj, "activated", icon_only=True, icon = "RESTRICT_RENDER_ON", emboss = False)

                rem = row.operator("meltdown.rem_job", text = "", icon = "X")
                rem.job_index = job_i            
                
                row = layout.row(align=True)
                row.alignment = 'EXPAND'
                row.prop(bj, 'resolution_x', text="X")
                row.prop(bj, 'resolution_y', text="Y")
                
                row = layout.row(align=True)
                row.alignment = 'EXPAND'
                row.prop(bj, 'antialiasing', text="4x Antialiasing")
                
                
                if bj.antialiasing == True:
                    row = layout.row(align=True)
                    row.alignment = 'EXPAND'
                    row.prop(bj, 'aa_sharpness', text="AA sharpness")
                
                row = layout.row(align=True)
                row.alignment = 'EXPAND'
                row.prop(bj, 'margin', text="Margin")
                
                
                row = layout.row(align=True)
                row.alignment = 'EXPAND'
                row.prop(bj, 'output', text="Path")
                
                row = layout.row(align=True)
                row.alignment = 'EXPAND'
                row.prop(bj, 'name', text="Name")
            
                for pair_i, pair in enumerate(bj.bake_queue):
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
                
                for pass_i, bakepass in enumerate(bj.bake_pass_queue):
                    row = layout.row(align=True)
                    row.alignment = 'EXPAND'
                    box = row.box().column(align=True)
                    
                    # box = layout.box().column(align=True)
                    #subrow = box.row(align=True)
                    #subrow.alignment = 'EXPAND'
                    #subrow.label(text=bakepass.get_filepath(bj = bj))
                    
                    subrow = box.row(align=True)
                    subrow.alignment = 'EXPAND'
                    subrow.prop(bakepass, 'pass_name')
                    box.separator()

                    subrow = box.row(align=True)
                    subrow.alignment = 'EXPAND'
                    subrow.prop(bakepass, 'influence', text="Texture influence")
                           
                    #subrow = box.row(align=True)
                    #subrow.alignment = 'EXPAND'
                    #subrow.prop(bakepass, 'suffix')
                    
                    if len(bakepass.props())>0:
                        subrow = box.row(align=True)
                        subrow.alignment = 'EXPAND'
                        
                        if "ao_distance" in bakepass.props():
                            subrow = box.row(align=True)
                            subrow.alignment = 'EXPAND'
                            subrow.prop(bakepass, 'ao_distance', text = "AO Distance")
                            
                        if "nm_space" in bakepass.props():
                            box.separator()
                            subrow = box.row(align=True)
                            subrow.alignment = 'EXPAND'
                            subrow.prop(bakepass, 'nm_space', text = "type")

                        if "swizzle" in bakepass.props():
                            box.separator()
                            subrow = box.row(align=True)
                            subrow.alignment = 'EXPAND'
                            subrow.label(text="Swizzle")
                            subrow.prop(bakepass, 'normal_r', text = "")
                            subrow.prop(bakepass, 'normal_g', text = "")
                            subrow.prop(bakepass, 'normal_b', text = "")
                            
                        if "samples" in bakepass.props():
                            subrow = box.row(align=True)
                            subrow.alignment = 'EXPAND'
                            subrow.prop(bakepass, 'samples', text = "Samples")    
                        
                        if "clean_environment" in bakepass.props():
                            subrow = box.row(align=True)
                            subrow.alignment = 'EXPAND'
                            subrow.prop(bakepass, 'clean_environment', text = "Clean Environment")
                        
                        if bakepass.clean_environment == False and "clean_environment" in bakepass.props():
                            subrow = box.row(align=True)
                            subrow.alignment = 'EXPAND'
                            subrow.prop(bakepass, 'environment_highpoly', text = "All Highpoly")  
                        
                        if bakepass.clean_environment == False and \
                        bakepass.environment_highpoly == False and \
                        "clean_environment" in bakepass.props():
                            subrow = box.row(align=True)
                            subrow.alignment = 'EXPAND'
                            subrow.prop_search(bakepass, "environment_group", bpy.data, "groups", text = "Environment")
                            
                    col = row.column()
                    row = col.row()
                    rem = row.operator("meltdown.rem_pass", text = "", icon = "X")
                    rem.pass_index = pass_i
                    rem.job_index = job_i
                    
                    row = col.row()
                    if bakepass.activated:
                        row.prop(bakepass, "activated", icon_only=True, icon = "RESTRICT_RENDER_OFF", emboss = False)
                    else:
                        row.prop(bakepass, "activated", icon_only=True, icon = "RESTRICT_RENDER_ON", emboss = False)

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
    register_class(MeltdownSettings)
    register_class(MeltdownSetup)     
    bpy.types.Scene.meltdown_setup = PointerProperty(type = MeltdownSetup)
    bpy.types.Scene.meltdown_settings = PointerProperty(type = MeltdownSettings)
    bpy.utils.register_module(__name__)
    bpy.types.Object.md_orig_name = bpy.props.StringProperty(name="Original Name")
    bpy.types.Group.md_orig_name = bpy.props.StringProperty(name="Original Name")
    bpy.types.World.md_orig_name = bpy.props.StringProperty(name="Original Name")
    bpy.types.Material.md_orig_name = bpy.props.StringProperty(name="Original Name")
     
    
def unregister():
    unregister_class(MeltdownSettings)
    unregister_class(MeltdownSetup)  
    unregister_class(BakePair)    
    unregister_class(BakePass)            
    unregister_class(BakeJob)
    bpy.utils.unregister_module(__name__)
    del bpy.types.Scene.meltdown_setup
    del bpy.types.Scene.meltdown_settings
    del bpy.types.Object.md_orig_name
    del bpy.types.Group.md_orig_name 
    del bpy.types.World.md_orig_name 
    del bpy.types.Material.md_orig_name
    print("Goodbye World!")
    

if __name__ == "__main__":
    register()  
if __name__ == "__main__":
    register()
