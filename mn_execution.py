import bpy, time
from bpy.app.handlers import persistent
from mn_utils import *
from mn_cache import clearExecutionCache
from mn_network_code_generator import getAllNetworkCodeStrings

ALLOW_COMPILING = True

compiledCodeObjects = []
codeStrings = []

def updateAnimationTrees(treeChanged = True):
	if ALLOW_COMPILING:
		forbidCompiling()
		start = time.clock()
		if treeChanged:
			rebuildNodeNetworks()
		for i, codeObject in enumerate(compiledCodeObjects):
			if bpy.context.scene.showFullError: 
				exec(codeObject, {})
			else:
				try: exec(codeObject, {})
				except BaseException as e:
					rebuildNodeNetworks()
					try: exec(codeObject, {})
					except BaseException as e: print(e)
		clearExecutionCache()
		if bpy.context.scene.printUpdateTime:
			timeSpan = time.clock() - start
			print("Exec. " + str(round(timeSpan, 7)) + " s  -  " + str(round(1/timeSpan, 5)) + " fps")
		allowCompiling()
			
def allowCompiling():
	global ALLOW_COMPILING
	ALLOW_COMPILING = True
def forbidCompiling():
	global ALLOW_COMPILING
	ALLOW_COMPILING = False
			
			
# compile code objects
################################

def rebuildNodeNetworks():
	global compiledCodeObjects, codeStrings
	del compiledCodeObjects[:]
	del codeStrings[:]
	try:
		codeStrings = getAllNetworkCodeStrings()
		for code in codeStrings:
			compiledCodeObjects.append(compile(code, "<string>", "exec"))
	except:
		pass
				
		
# Force Cache Rebuilding Panel
##############################
		
class AnimationNodesPanel(bpy.types.Panel):
	bl_idname = "mn.panel"
	bl_label = "Animation Nodes"
	bl_space_type = "NODE_EDITOR"
	bl_region_type = "UI"
	bl_context = "objectmode"
	
	def draw(self, context):
		layout = self.layout
		layout.operator("mn.force_full_update")
		layout.operator("mn.print_node_tree_execution_string")
		scene = context.scene
		layout.label("Update when:")
		layout.prop(scene, "updateAnimationTreeOnFrameChange", text = "Frames Changes")
		layout.prop(scene, "updateAnimationTreeOnSceneUpdate", text = "Scene Updates")
		layout.prop(scene, "updateAnimationTreeOnPropertyChange", text = "Property Changes")
		layout.prop(scene, "printUpdateTime", text = "Print Update Time")
		layout.prop(scene, "showFullError", text = "Show Full Error")
		layout.prop(scene, "nodeExecutionProfiling", text = "Node Execution Profiling")
		
		layout.operator("mn.load_normal_node_template")
		layout.operator("mn.append_auto_update_code")
		layout.prop(scene, "customNodeCategory")
		customNodeClasses = getCustomNodesInCategory(scene.customNodeCategory)
		for nodeClass in customNodeClasses:
			newNode = layout.operator("node.add_node", text = nodeClass.bl_label)
			newNode.type = nodeClass.bl_idname
			newNode.use_transform = True
		
		
		
class ForceNodeTreeUpdate(bpy.types.Operator):
	bl_idname = "mn.force_full_update"
	bl_label = "Force Node Tree Update"

	def execute(self, context):
		updateAnimationTrees(treeChanged = True)
		return {'FINISHED'}
		
class PrintNodeTreeExecutionStrings(bpy.types.Operator):
	bl_idname = "mn.print_node_tree_execution_string"
	bl_label = "Print Node Tree Code"

	def execute(self, context):
		print()
		for codeString in codeStrings:
			print(codeString)
			print()
			print("-"*80)
			print()
		return {'FINISHED'}
		
class LoadNormalNodeTemplate(bpy.types.Operator):
	bl_idname = "mn.load_normal_node_template"
	bl_label = "Load Normal Node Template"

	def execute(self, context):
		from mn_node_template import getNormalNodeTemplate, getAutoRegisterCode
		textBlockName = "mn_node_template.py"
		textBlock = bpy.data.texts.get(textBlockName)
		if textBlock is None:
			textBlock = bpy.data.texts.new(textBlockName)
		textBlock.clear()
		textBlock.write(getNormalNodeTemplate())
		textBlock.write(getAutoRegisterCode())
		return {'FINISHED'}
		
class AppendAutoUpdateCode(bpy.types.Operator):
	bl_idname = "mn.append_auto_update_code"
	bl_label = "Append Auto Update Code"

	def execute(self, context):
		from mn_node_template import getAutoRegisterCode
		for area in bpy.context.screen.areas:
			for space in area.spaces:
				if space.type == "TEXT_EDITOR":
					if space.text is not None:
						textString = space.text.as_string()
						textString += getAutoRegisterCode()
						space.text.from_string(textString)
		return {'FINISHED'}
	
	
		
# handlers to start the update
##############################

bpy.types.Scene.updateAnimationTreeOnFrameChange = bpy.props.BoolProperty(default = True, name = "Update Animation Tree On Frame Change")
bpy.types.Scene.updateAnimationTreeOnSceneUpdate = bpy.props.BoolProperty(default = True, name = "Update Animation Tree On Scene Update")
bpy.types.Scene.updateAnimationTreeOnPropertyChange = bpy.props.BoolProperty(default = True, name = "Update Animation Tree On Property Change")

bpy.types.Scene.printUpdateTime = bpy.props.BoolProperty(default = False, name = "Print Update Time")
bpy.types.Scene.showFullError = bpy.props.BoolProperty(default = False, name = "Show Full Error")
bpy.types.Scene.nodeExecutionProfiling = bpy.props.BoolProperty(default = False, name = "Node Execution Profiling")

def getAllAnimationNodeClasses():
	from mn_node_base import AnimationNode
	return AnimationNode.__subclasses__()
def getCustomNodeClasses():
	from mn_node_register import getAllNodeIdNames
	officialNodeNames = getAllNodeIdNames()
	nodeClasses = []
	foundNames = []
	for nodeClass in getAllAnimationNodeClasses():
		if nodeClass.bl_idname not in officialNodeNames and nodeClass.bl_idname not in foundNames:
			nodeClasses.append(nodeClass)
			foundNames.append(nodeClass.bl_idname)
	return nodeClasses
def getCustomCategories():
	nodeClasses = getCustomNodeClasses()
	categories = set()
	for nodeClass in nodeClasses:
		category = getattr(nodeClass, "node_category", "None")
		categories.update([category])
	if len(categories) == 0: categories.update(["None"])
	return categories
def getCustomNodeCategoryItems(self, context):
	categories = getCustomCategories()
	items = []
	for category in categories:
		items.append((category, category, ""))
	return items
	
def getCustomNodesInCategory(category):
	nodeClasses = getCustomNodeClasses()
	nodeClassesInCategory = []
	for nodeClass in nodeClasses:
		if getattr(nodeClass, "node_category", "None") == category:
			nodeClassesInCategory.append(nodeClass)
	return nodeClassesInCategory

def getCustomNodes(self, context):
	return [("mn_TimeInfoNode", "Time Info", "")]
	
bpy.types.Scene.customNodeName = bpy.props.EnumProperty(items = getCustomNodes, name = "Custom Node Name")
bpy.types.Scene.customNodeCategory = bpy.props.EnumProperty(items = getCustomNodeCategoryItems, name = "Custom Categories")
	
@persistent
def frameChangeHandler(scene):
	if scene.updateAnimationTreeOnFrameChange:
		updateAnimationTrees(False)
@persistent
def sceneUpdateHandler(scene):
	if scene.updateAnimationTreeOnSceneUpdate:
		updateAnimationTrees(False)
@persistent
def fileLoadHandler(scene):
	updateAnimationTrees(True)
def nodePropertyChanged(self, context):
	if context.scene.updateAnimationTreeOnPropertyChange:
		updateAnimationTrees(False)
def nodeTreeChanged():
	updateAnimationTrees(True)

	
bpy.app.handlers.frame_change_post.append(frameChangeHandler)
bpy.app.handlers.scene_update_post.append(sceneUpdateHandler)
bpy.app.handlers.load_post.append(fileLoadHandler)