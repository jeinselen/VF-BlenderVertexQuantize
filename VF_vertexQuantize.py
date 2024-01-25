bl_info = {
	"name": "VF Vertex Quantize",
	"author": "John Einselen - Vectorform LLC",
	"blender": (2, 83, 0),
	"location": "Scene > VF Tools > Vertex Quantize",
	"version": (0, 3, 0),
	"description": "Customisable vertex snapping for increments that don't match the default grid scale",
	"warning": "inexperienced developer, use at your own risk",
	"doc_url": "https://github.com/jeinselenVF/VF-BlenderVertexQuantize",
	"tracker_url": "https://github.com/jeinselenVF/VF-BlenderVertexQuantize/issues",
	"category": "3D View"}

# Based in part on basic code found here:
# https://blenderartists.org/t/move-selected-vertices-with-python-script/1303114
# https://blender.stackexchange.com/questions/196483/create-keyboard-shortcut-for-an-operator-using-python

import bpy

###########################################################################
# Main class

class vf_vertex_quantize(bpy.types.Operator):
	bl_idname = "vfvertexquantize.offset"
	bl_label = "Vertex Quantize"
	bl_description = "Snap vertices to custom quantization steps"
	bl_options = {'REGISTER', 'UNDO'}
	
	def execute(self, context):
		# self.report({'INFO'}, f"This is {self.bl_idname}")
		if not bpy.context.view_layer.objects.active.data.vertices:
			print("Error in VF Vertex Quantize operation (data not available?)")
			return {'CANCELLED'}
		
		# Set up local variables
		if bpy.context.scene.vf_quantize_settings.vert_dimensions == 'True':
			quantX = quantY = quantZ = bpy.context.scene.vf_quantize_settings.vert_uniform
		else:
			quantX = bpy.context.scene.vf_quantize_settings.vert_xyz[0] # X quantization
			quantY = bpy.context.scene.vf_quantize_settings.vert_xyz[1] # Y quantization
			quantZ = bpy.context.scene.vf_quantize_settings.vert_xyz[2] # Z quantization
		# source = bpy.context.view_layer.objects.active.data.vertices
		
		# Begin code modified from Scriblab and Photox source on BlenderArtist https://blenderartists.org/t/move-selected-vertices-with-python-script/1303114
		mode = bpy.context.active_object.mode
		bpy.ops.object.mode_set(mode='OBJECT')
		selectedVerts = [v for v in bpy.context.active_object.data.vertices if v.select]
		
		# Process vertices
		for vert in selectedVerts:
			new_location = vert.co
			if quantX > 0.0:
				new_location[0] = round(new_location[0] / quantX) * quantX
			if quantY > 0.0:
				new_location[1] = round(new_location[1] / quantY) * quantY
			if quantZ > 0.0:
				new_location[2] = round(new_location[2] / quantZ) * quantZ
			vert.co = new_location
		
		# Reset object mode to original
		bpy.ops.object.mode_set(mode=mode)

		# Done
		return {'FINISHED'}

###########################################################################
# Project settings and UI rendering classes

class vfQuantizeSettings(bpy.types.PropertyGroup):
	vert_dimensions: bpy.props.EnumProperty(
		name='Vertex Quantization',
		description='Planar projection coordinate space',
		items=[
			('True', 'Uniform', 'Use uniform XYZ dimension snapping'),
			('False', 'Separate', 'Use non-uniform snapping with separate XYZ values')
			],
		default='True')
	vert_uniform: bpy.props.FloatProperty(
		name="Uniform Quantization Value",
		description="Uniform snapping across XYZ axis",
		subtype="DISTANCE",
		default=0.025,
		step=1.25,
		precision=3,
		min=0.0,
		soft_min=0.0,
		soft_max=1.0)
	vert_xyz: bpy.props.FloatVectorProperty(
		name="XYZ Quantization",
		description="XYZ snapping distances",
		subtype="TRANSLATION",
		size=3,
		default=[0.025, 0.025, 0.025],
		step=1.25,
		precision=3,
		min=0,
		soft_min=0.0,
		soft_max=1.0)

class VFTOOLS_PT_vertex_quantize(bpy.types.Panel):
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = 'VF Tools'
	bl_order = 8
	bl_options = {'DEFAULT_CLOSED'}
	bl_label = "Vertex Quantize"
	bl_idname = "VFTOOLS_PT_vertex_quantize"
	
	@classmethod
	def poll(cls, context):
		return True
	
	def draw_header(self, context):
		try:
			layout = self.layout
		except Exception as exc:
			print(str(exc) + " | Error in VF Vertex Quantize panel header")
	
	def draw(self, context):
		try:
			layout = self.layout
			layout.use_property_decorate = False # No animation
			
			col = layout.column(align=True)
			row = col.row(align=True)
			row.prop(context.scene.vf_quantize_settings, 'vert_dimensions', expand=True)
			if bpy.context.scene.vf_quantize_settings.vert_dimensions == 'True':
				col.prop(context.scene.vf_quantize_settings, 'vert_uniform', text='')
			else:
				row = col.row(align=True)
				row.prop(context.scene.vf_quantize_settings, 'vert_xyz', text='')

			# if bpy.context.view_layer.objects.active.data.vertices:
			if bpy.context.view_layer.objects.active and bpy.context.view_layer.objects.active.type == "MESH":
				layout.operator(vf_vertex_quantize.bl_idname)
			else:
				box = layout.box()
				box.label(text="Active object must be a mesh with selected vertices")
		except Exception as exc:
			print(str(exc) + " | Error in VF Vertex Quantize panel")

classes = (vf_vertex_quantize, vfVertexQuantizeSettings, VFTOOLS_PT_vertex_quantize)
addon_keymaps = []

###########################################################################
# Addon registration functions

def register():
	for cls in classes:
		bpy.utils.register_class(cls)
	bpy.types.Scene.vf_quantize_settings = bpy.props.PointerProperty(type=vfQuantizeSettings)

	# Add the hotkey
	wm = bpy.context.window_manager
	kc = wm.keyconfigs.addon
	if kc:
		km = wm.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')
		kmi = km.keymap_items.new(vf_vertex_quantize.bl_idname, type='Q', value='PRESS', shift=True)
		addon_keymaps.append((km, kmi))

def unregister():
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)
	del bpy.types.Scene.vf_quantize_settings

	# Remove the hotkey
	for km, kmi in addon_keymaps:
		km.keymap_items.remove(kmi)
	addon_keymaps.clear()

if __name__ == "__main__":
	register()