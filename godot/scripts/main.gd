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
var post_mat: ShaderMaterial
var shot_path := ""
var shot_frames := 0
var shot_scene := -1
var _frame := 0


func _ready() -> void:
	_setup_input()
	hud = HUD.new()
	add_child(hud)
	env = WorldEnvironment.new()
	add_child(env)
	sun = DirectionalLight3D.new()
	sun.shadow_enabled = true
	add_child(sun)
	var ua := OS.get_cmdline_user_args()
	for i in ua.size():
		if ua[i] == "--shot" and i + 1 < ua.size():
			shot_path = _abs(ua[i + 1])
		if ua[i] == "--frames" and i + 1 < ua.size():
			shot_frames = int(ua[i + 1])
		if ua[i] == "--scene" and i + 1 < ua.size():
			shot_scene = int(ua[i + 1])
	if shot_path != "" and shot_frames == 0:
		shot_frames = 90
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
	_enter_scene(max(0, shot_scene))


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
	mat.set_shader_parameter("light_tint", Vector3(tint[0], tint[1], tint[2]))
	var skyd: Dictionary = sc["sky"]
	var sh0: Array = skyd.get("shadow_tint", [0.7, 0.74, 0.86])
	mat.set_shader_parameter("shadow_tint", Vector3(sh0[0], sh0[1], sh0[2]))
	var is_indoor: bool = sc.get("interior", false)
	var sd: Array = skyd.get("sun_dir", [-0.4, -0.8, -0.4])
	# interiors: a soft key from the lamp overhead / window side; exteriors: the mood sun
	mat.set_shader_parameter("key_dir", Vector3(-0.35, -1.0, -0.55) if is_indoor else Vector3(sd[0], sd[1], sd[2]))
	var mood0: String = sc.get("mood", "DAY")
	mat.set_shader_parameter("shadow_value", 0.62 if is_indoor else {"DAY": 0.6, "GOLDEN": 0.55, "DUSK": 0.5, "NIGHT": 0.45}.get(mood0, 0.55))
	mat.set_shader_parameter("debug_albedo", OS.get_cmdline_user_args().has("--debug-albedo"))
	if OS.get_cmdline_user_args().has("--debug-lights"):
		var nl := 0
		for n in root.find_children("*", "Light3D", true, false):
			print("LIGHT ", n.name, " ", n.get_class(), " e=", n.light_energy, " c=", n.light_color, " at ", n.global_position)
			nl += 1
		print("LIGHTS ", nl)
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
			if l is OmniLight3D:                       # glTF candela -> calm game lamps
				var indoor: bool = world["scenes"][scene_index].get("interior", false)
				l.light_energy = 2.4 if indoor else 1.4
				if indoor:
					var ltw: Array = world["scenes"][scene_index]["sky"].get("light_tint", [1, 0.9, 0.75])
					l.light_color = Color(ltw[0], ltw[1], ltw[2])
				(l as OmniLight3D).omni_range = 9.0 if indoor else 7.0
			elif l is SpotLight3D:
				l.light_energy = 1.0


func _apply_weather(sc: Dictionary) -> void:
	if post_mat == null:
		return
	var w: String = sc.get("layers", {}).get("weather", "clear")
	post_mat.set_shader_parameter("weather", {"rain": 1, "snow": 2, "fog": 3, "storm": 4}.get(w, 0))
	post_mat.set_shader_parameter("mist", {"rain": 0.15, "snow": 0.2, "fog": 0.6, "storm": 0.3, "heat-haze": 0.1}.get(w, 0.0))


func _setup_environment(sc: Dictionary) -> void:
	_apply_weather(sc)
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
	var lt0: Array = s.get("light_tint", [1, 1, 1])
	var shc := Color(sh[0], sh[1], sh[2])
	if sc.get("interior", false):                  # lamp-lit rooms: warm fill, never a blue cave
		e.ambient_light_color = shc.lerp(Color(lt0[0], lt0[1], lt0[2]), 0.5) * 0.75
	else:
		e.ambient_light_color = shc * 0.62
	e.ambient_light_energy = 1.0
	e.ambient_light_sky_contribution = 0.0       # ambient = our shadow/lamp tint, not the night sky
	e.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	env.environment = e
	var d: Array = s["sun_dir"]
	var dirv := Vector3(d[0], d[1], d[2]).normalized()
	sun.look_at_from_position(Vector3.ZERO, dirv, Vector3.UP if abs(dirv.y) < 0.99 else Vector3.FORWARD)
	var mood: String = sc.get("mood", "DAY")
	sun.light_energy = {"DAY": 1.3, "GOLDEN": 1.1, "DUSK": 0.8, "NIGHT": 0.25}.get(mood, 1.0)
	var lt: Array = s.get("light_tint", [1, 1, 1])
	sun.light_color = Color(lt[0], lt[1], lt[2]) if mood != "NIGHT" else Color(0.6, 0.68, 0.85)
	if sc.get("interior", false) and mood in ["DUSK", "NIGHT"]:
		sun.light_energy = 0.0


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
	pm.set_shader_parameter("ink", Vector3(0.02, 0.017, 0.015))
	pm.set_shader_parameter("paper", Vector3(0.95, 0.91, 0.82))
	q.material_override = pm
	post_mat = pm
	_apply_weather(world["scenes"][scene_index])
	var ua := OS.get_cmdline_user_args()
	if ua.has("--debug-edges"):
		pm.set_shader_parameter("debug_mode", 1)
	if ua.has("--debug-raw"):
		pm.set_shader_parameter("debug_mode", 2)
	q.position = Vector3(0, 0, -0.5)
	cam.add_child(q)


# ------------------------------------------------------------------ story flow
func _process(_delta: float) -> void:
	_frame += 1
	if shot_path != "" and _frame == shot_frames:      # test hook: screenshot + quit
		get_viewport().get_texture().get_image().save_png(shot_path)
		print("SHOT ", shot_path)
		get_tree().quit()
	if player == null or world.is_empty():
		return
	var sc: Dictionary = world["scenes"][scene_index]
	var beats: Array = sc["beats"]
	# beats fire in order when the player reaches the next one's trigger (the first fires on entry)
	if next_beat < beats.size():
		var b: Dictionary = beats[next_beat]
		var t: Array = b["trigger"]["pos"]
		var r: float = float(b["trigger"]["radius_m"]) * (0.55 if sc.get("interior", false) else 1.0)
		var near := player.global_position.distance_to(Vector3(t[0], t[1], t[2])) < r
		if next_beat == 0 or (near and not hud._busy):
			hud.show_beat(b)
			next_beat += 1
			if next_beat < beats.size():
				var f = beats[next_beat]["trigger"].get("focus")
				hud.set_prompt(("Find: %s" % String(f).replace("_", " ")) if f else "")
	else:
		var last: bool = scene_index + 1 >= world["scenes"].size()
		hud.set_prompt("THE END" if last else "Press E to continue the story")
		if not last and Input.is_action_just_pressed("interact"):
			hud.ink_wipe(func(): _enter_scene(scene_index + 1))
	if Input.is_action_just_pressed("next_scene") and scene_index + 1 < world["scenes"].size():
		hud.ink_wipe(func(): _enter_scene(scene_index + 1))
