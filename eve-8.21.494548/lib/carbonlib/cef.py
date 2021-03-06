#Embedded file name: c:\depot\games\branches\release\EVE-TRANQUILITY\carbon\common\lib\cef.py
SCHEMA = 'zentity'
_PREFIX = 'zentity.'
INGREDIENT_INITS_TABLE_FULL_NAME = _PREFIX + 'ingredientInitialValues'
INGREDIENTS_TABLE_FULL_NAME = _PREFIX + 'ingredients'
SPAWNS_TABLE_FULL_NAME = _PREFIX + 'spawns'
GROUP_TABLE_FULL_NAME = _PREFIX + 'groups'
SPAWN_GROUP_TABLE_FULL_NAME = _PREFIX + 'spawnGroups'
SPAWN_GROUP_LINK_TABLE_FULL_NAME = _PREFIX + 'spawnGroupLinks'
RECIPES_TABLE_FULL_NAME = _PREFIX + 'recipes'
ALL_TABLES = [INGREDIENT_INITS_TABLE_FULL_NAME, INGREDIENTS_TABLE_FULL_NAME, SPAWNS_TABLE_FULL_NAME]
PARENT_TYPEID = 0
PARENT_GROUPID = 1
PARENT_CATEGORYID = 2
PARENT_SPAWNID = 3
ALL_PARENT_TYPES = [PARENT_TYPEID,
 PARENT_GROUPID,
 PARENT_CATEGORYID,
 PARENT_SPAWNID]
NPC_ROOT_RECIPE = 9
SPAWN_TYPE_ACTIVE_ON_LOAD = 0
SPAWN_TYPE_DYNAMICALLY_ACTIVATED = 1
SPAWN_TYPE_NAMES = {SPAWN_TYPE_ACTIVE_ON_LOAD: 'Active on load',
 SPAWN_TYPE_DYNAMICALLY_ACTIVATED: 'Activated dynamically'}
SELECT_RECIPE = 'cef_SelectRecipe'
SELECT_SPAWN_GROUP = 'SelectSpawnGroup'
SELECT_NPC_ENCOUNTER = 'SelectNpcEncounter'
ENTITY_STATE_UNINITIALIZED = 0
ENTITY_STATE_CREATING = 1
ENTITY_STATE_READY = 2
ENTITY_STATE_DESTROYING = 3
ENTITY_STATE_DEAD = 4
ENTITY_STATE_NAMES = {ENTITY_STATE_UNINITIALIZED: 'Uninitialized',
 ENTITY_STATE_CREATING: 'Creating',
 ENTITY_STATE_READY: 'Ready',
 ENTITY_STATE_DESTROYING: 'Destroying',
 ENTITY_STATE_DEAD: 'Dead'}
INVALID_COMPONENT_ID = None
JESSICA_SELECTION_COMPONENT_ID = -1
JESSICA_ENCOUNTER_COMPONENT_ID = -2
PLAYER_COMPONENT_ID = 1
MOVEMENT_COMPONENT_ID = 2
POSITION_COMPONENT_ID = 3
BOUNDING_VOLUME_COMPONENT_ID = 4
PAPER_DOLL_COMPONENT_ID = 5
APERTURE_COMPONENT_ID = 6
PROXIMITY_TRIGGER_COMPONENT_ID = 7
ANIMATION_COMPONENT_ID = 8
ACTION_COMPONENT_ID = 9
PERCEPTION_COMPONENT_ID = 10
AUDIO_EMMITTER_COMPONENT_ID = 12
COLLISION_MESH_COMPONENT_ID = 14
AIMING_COMPONENT_ID = 18
APERTURE_SUBJECT_COMPONENT_ID = 19
SIMPLE_TEST_COMPONENT_ID = 20
ACTION_OBJECT_COMPONENT_ID = 21
SELECTION_COMPONENT_ID = 22
DECISION_TREE_COMPONENT_ID = 23
INFO_COMPONENT_ID = 24
BUFF_COMPONENT_ID = 51
MODIFIER_COMPONENT_ID = 52
PROXIMITY_COMPONENT_ID = 55
LENS_FLARE_COMPONENT_ID = 56
UIDESKTOP_COMPONENT_ID = 57
INTERIOR_STATIC_COMPONENT_ID = 58
PARTICLE_OBJECT_COMPONENT_ID = 59
INTERIOR_PLACEABLE_COMPONENT_ID = 60
LOADED_LIGHT_COMPONENT_ID = 61
LIGHT_ANIMATION_COMPONENT_ID = 62
BATMA_ATTRIBUTES_COMPONENT_ID = 63
HIGHLIGHT_COMPONENT_ID = 64
PHYSICAL_PORTAL_COMPONENT_ID = 65
BATMA_BUFFS_COMPONENT_ID = 66
BATMA_MODIFIERS_COMPONENT_ID = 67
BATMA_EFFECTS_COMPONENT_ID = 68
POINT_LIGHT_COMPONENT_ID = 69
SPOT_LIGHT_COMPONENT_ID = 70
BOX_LIGHT_COMPONENT_ID = 71
UV_PICKING_COMPONENT_ID = 72
OCCLUDER_COMPONENT_ID = 73
HATE_COMPONENT_ID = 74
BENCHMARK_CAMERA_COMPONENT_ID = 75
BENCHMARK_AVATAR_COMPONENT_ID = 76
CYLINDER_LIGHT_COMPONENT_ID = 77
DIRECTIONAL_LIGHT_COMPONENT_ID = 78
JESSICA_TEXT_COMPONENT_ID = 79
COMPONENTDATA_INVALID_TYPE = 0
COMPONENTDATA_ID_TYPE = 1
COMPONENTDATA_STRING_TYPE = 2
COMPONENTDATA_INT_TYPE = 3
COMPONENTDATA_FLOAT_TYPE = 4
COMPONENTDATA_BOOL_TYPE = 5
COMPONENTDATA_NON_PRIMITIVE_TYPE = 6
COMPONENTDATA_ARBITRARY_DROPDOWN_TYPE = 8
COMPONENTDATA_FLOAT_VECTOR_AS_STRING_TYPE = 10001
COMPONENTDATA_GRAPHIC_ID_TYPE = 10002
COMPONENTDATA_CELL_TYPE = 10004
COMPONENTDATA_COLOR_TYPE = 10005
COMPONENTDATA_KELVIN_COLOR_TYPE = 10006
COMPONENTDATA_PORTAL_CELL_TYPE = 10007
LIGHT_VISUALIZATION = 0
PHYSICAL_PORTAL_VISUALIZATION = 1
OCCLUDER_VISUALIZATION = 2
COLLISION_VISUALIZATION = 3
AUDIO_VISUALIZATION = 4
PAPERDOLL_VISUALIZATION = 5
LENS_FLARE_VISUALIZATION = 6
PARTICLE_VISUALIZATION = 7
RUNTIME_ENTITYID_OFFSET = 9900000000000000000L
RECIPE_NAME_STATICS = 'Static Graphics'
RECIPE_NAME_PLACEABLES = 'Placeable Graphics'