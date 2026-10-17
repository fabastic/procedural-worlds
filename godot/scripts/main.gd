## Walk the story: loads story_out/<slug>/world/world.json + the scene GLBs Blender built
## (tools/build_world.py), dresses them in the ink look, and plays the beats as the player walks.
##   godot --path godot -- --story ../story_out/the-last-watch/world
## With no --story argument a picker lists every story folder under ../story_out that has a world.
extends Node3D

const TOON := preload("res://shaders/ink_toon.gdshader")
const POST := preload("res://shaders/ink_post.gdshader")
const SKY := preload("res://shaders/sky.gdshader")
const PLAYER := preload("res://scripts/player.gd")
const HUD := preload("res://scripts/hud.gd")

var world: Dictionary = {}
var world_dir := ""
var scene_index := 0
var level: Node3D
var player: CharacterBody3D
var hud: CanvasLayer
var env: WorldEnvironment
var sun: DirectionalLight3D
var fired := {}
var next_beat := 0
var focus_nodes := {}


func _ready() -> void:
	_setup_input()
	hud = HUD.new()
	add_child(hud)
	env = WorldEnvironment.new()
	add_child(env)
	sun = DirectionalLight3D.new()
	sun.shadow_enabled = true
	add_child(sun)
	var dir := _story_arg()
	if dir == "":
		_show_picker()
	else:
		_load_world(dir)


func _setup_input() -> void:
	var keys := {"move_forward": KEY_W, "move_back": KEY_S, "move_left": KEY_A, "move_right": KEY_D,
				 "interact": KEY_E, "sprint": KEY_SHIFT, "next_scene": KEY_N}
	for a in keys:
		if not InputMap.has_action(a):
			InputMap.add_action(a)
			var ev := InputEventKey.new()
			ev.physical_keycode = keys[a]
			InputMap.action_add_event(a, ev)
	for pair in [["move_forward", KEY_UP], ["move_back", KEY_DOWN], ["move_left", KEY_LEFT], ["move_right", KEY_RIGHT]]:
		var ev2 := InputEventKey.new()
		ev2.physical_keycode = pair[1]
		InputMap.action_add_event(pair[0], ev2)


func _story_arg() -> String:
	var a := OS.get_cmdline_user_args()
	for i in a.size():
		if a[i] == "--story" and i + 1 < a.size():
			return _abs(a[i + 1])
		if a[i].begins_with("--story="):
			return _abs(a[i].substr(8))
	return ""


func _abs(p: String) -> String:
	if p.is_absolute_path():
		return p
	return ProjectSettings.globalize_path("res://").path_join(p).simplify_path()


func _stories_root() -> String:
	return ProjectSettings.globalize_path("res://").path_join("../story_out").simplify_path()


# ------------------------------------------------------------------ story picker
func _show_picker() -> void:
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	var box := VBoxContainer.new()
	box.position = Vector2(60, 60)
	box.add_theme_constant_override("separation", 12)
	var title := Label.new()
	title.text = "PROCEDURAL WORLDS - WALK THE STORY"
	title.add_theme_font_size_override("font_size", 34)
	box.add_child(title)
	var d := DirAccess.open(_stories_root())
	var found := 0
	if d:
		for slug in d.get_directories():
			var wj := _stories_root().path_join(slug).path_join("world/world.json")
			if FileAccess.file_exists(wj):
				var b := Button.new()
				var w: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(wj))
				b.text = "  %s  -  %s" % [w.get("title", slug), w.get("logline", "")]
				b.pressed.connect(func(): box.queue_free(); _load_world(wj.get_base_dir()))
				box.add_child(b)
				found += 1
	if found == 0:
		var l := Label.new()
		l.text = "No built worlds in %s.\nRun: tools/blender.sh -b --factory-startup -P tools/build_world.py -- story/examples/<story>.json" % _stories_root()
		box.add_child(l)
	hud.add_child(box)


# ------------------------------------------------------------------ world loading
func _load_world(dir: String) -> void:
	world_dir = dir
	var txt := FileAccess.get_file_as_string(dir.path_join("world.json"))
	world = JSON.parse_string(txt)
	if world == null or not world.has("scenes"):
		push_error("Bad world.json in " + dir)
		return
	hud.show_title(String(world.get("title", "")).to_upper(), 3.0)
	_enter_scene(0)


func _enter_scene(i: int) -> void:
	scene_index = i
	if level:
		level.queue_free()
	focus_nodes.clear()
	fired.clear()
	next_beat = 0
	var sc: Dictionary = world["scenes"][i]
	var doc := GLTFDocument.new()
	var state := GLTFState.new()
	var err := doc.append_from_file(world_dir.path_join(sc["glb"]), state)
	if err != OK:
		push_error("Could not load " + sc["glb"])
		return
	level = doc.generate_scene(state)
	add_child(level)
	_dress(level)
	_setup_environment(sc)
	if player == null:
		player = PLAYER.new()
		player.eye_height = float(world.get("protagonist", {}).get("eye_height_m", 1.65))
		add_child(player)
		_add_post(player.camera)
	respawn()
	hud.show_title(String(sc.get("name", sc["id"])).to_upper(), 2.0)


func respawn() -> void:
	var sc: Dictionary = world["scenes"][scene_index]
	var p: Array = sc["spawn"]["pos"]
	player.global_position = Vector3(p[0], p[1] + 0.05, p[2])
	player.rotation = Vector3(0, deg_to_rad(float(sc["spawn"].get("yaw_deg", 0.0))), 0)
	player.velocity = Vector3.ZERO


## Ink-toon every mesh (vertex colours carry the baked ink palette), collide with everything that
## isn't marked __nocol, and remember focus empties for interaction.
func _dress(root: Node) -> void:
	var sc: Dictionary = world["scenes"][scene_index]
	var tint: Array = sc["sky"].get("light_tint", [1, 1, 1])
	var mat := ShaderMaterial.new()
	mat.shader = TOON
	mat.set_shader_parameter("light_tint", Color(tint[0], tint[1], tint[2]))
	var stack: Array = [root]
	while not stack.is_empty():
		var n: Node = stack.pop_back()
		stack.append_array(n.get_children())
		if n is MeshInstance3D:
			var mi: MeshInstance3D = n
			mi.material_override = mat
			if not String(mi.name).contains("__nocol") and mi.mesh:
				var body := StaticBody3D.new()
				var cs := CollisionShape3D.new()
				cs.shape = mi.mesh.create_trimesh_shape()
				body.add_child(cs)
				mi.add_child(body)
		elif n is Node3D and String(n.name).begins_with("PW_Focus_"):
			focus_nodes[String(n.name).substr(9)] = n
		elif n is Light3D:
			var l: Light3D = n
			l.shadow_enabled = l is OmniLight3D
			if l is OmniLight3D:
				l.light_energy = clampf(l.light_energy, 0.0, 16.0)


func _setup_environment(sc: Dictionary) -> void:
	var s: Dictionary = sc["sky"]
	var e := Environment.new()
	e.background_mode = Environment.BG_SKY
	var sky := Sky.new()
	var skm := ShaderMaterial.new()
	skm.shader = SKY
	skm.set_shader_parameter("top", _col(s["top"]))
	skm.set_shader_parameter("horizon", _col(s["horizon"]))
	skm.set_shader_parameter("cloud", _col(s["cloud"]))
	skm.set_shader_parameter("below", _col(s["horizon"]) * 0.6)
	sky.sky_material = skm
	e.sky = sky
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	var sh: Array = s.get("shadow_tint", [0.6, 0.62, 0.75])
	e.ambient_light_color = Color(sh[0], sh[1], sh[2]) * (0.55 if not sc.get("interior", false) else 0.45)
	e.ambient_light_energy = 1.0
	e.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	env.environment = e
	var d: Array = s["sun_dir"]
	var dirv := Vector3(d[0], d[1], d[2]).normalized()
	sun.look_at_from_position(Vector3.ZERO, dirv, Vector3.UP if abs(dirv.y) < 0.99 else Vector3.FORWARD)
	sun.light_energy = 1.2 if sc.get("mood", "DAY") != "NIGHT" else 0.45
	sun.visible = not sc.get("interior", false) or true


func _col(a: Array) -> Color:
	return Color(a[0], a[1], a[2])


func _add_post(cam: Camera3D) -> void:
	var q := MeshInstance3D.new()
	var qm := QuadMesh.new()
	qm.size = Vector2(2, 2)
	q.mesh = qm
	q.extra_cull_margin = 16384.0
	var pm := ShaderMaterial.new()
	pm.shader = POST
	q.material_override = pm
	q.position = Vector3(0, 0, -0.5)
	cam.add_child(q)


# ------------------------------------------------------------------ story flow
func _process(_delta: float) -> void:
	if player == null or world.is_empty():
		return
	var sc: Dictionary = world["scenes"][scene_index]
	var beats: Array = sc["beats"]
	# beats fire in order when the player reaches the next one's trigger (the first fires on entry)
	if next_beat < beats.size():
		var b: Dictionary = beats[next_beat]
		var t: Array = b["trigger"]["pos"]
		var near := player.global_position.distance_to(Vector3(t[0], t[1], t[2])) < float(b["trigger"]["radius_m"]) + 1.0
		if next_beat == 0 or near:
			hud.show_beat(b)
			next_beat += 1
			if next_beat < beats.size():
				var f = beats[next_beat]["trigger"].get("focus")
				hud.set_prompt(("Find: %s" % String(f).replace("_", " ")) if f else "")
	else:
		var last := scene_index + 1 >= world["scenes"].size()
		hud.set_prompt("THE END" if last else "Press E to continue the story")
		if not last and Input.is_action_just_pressed("interact"):
			hud.ink_wipe(func(): _enter_scene(scene_index + 1))
	if Input.is_action_just_pressed("next_scene") and scene_index + 1 < world["scenes"].size():
		hud.ink_wipe(func(): _enter_scene(scene_index + 1))
