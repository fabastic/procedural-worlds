## Inked HUD: narration caption boxes (cream, black border, slight tilt), off-panel speech balloons,
## an interact prompt, a scene title card and the ink-blot wipe used between scenes.
extends CanvasLayer

const CREAM := Color(0.97, 0.93, 0.80)
const INK := Color(0.04, 0.035, 0.03)

var caption_box: PanelContainer
var caption_label: Label
var balloons: VBoxContainer
var prompt: Label
var title_card: Label
var wipe: ColorRect
var _queue: Array = []
var _busy := false


func _ready() -> void:
	caption_box = _panel(CREAM)
	caption_box.position = Vector2(28, 24)
	caption_box.rotation_degrees = -0.8
	caption_label = _label(22)
	caption_box.add_child(caption_label)
	caption_box.visible = false
	add_child(caption_box)
	balloons = VBoxContainer.new()
	balloons.anchor_left = 1.0
	balloons.anchor_right = 1.0
	balloons.offset_left = -470
	balloons.offset_right = -28
	balloons.offset_top = 380
	balloons.add_theme_constant_override("separation", 10)
	add_child(balloons)
	prompt = _label(18)
	prompt.anchor_top = 1.0
	prompt.anchor_bottom = 1.0
	prompt.anchor_left = 0.5
	prompt.offset_top = -64
	prompt.offset_left = -200
	prompt.custom_minimum_size = Vector2(400, 0)
	prompt.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	prompt.add_theme_color_override("font_color", CREAM)
	prompt.add_theme_color_override("font_outline_color", INK)
	prompt.add_theme_constant_override("outline_size", 6)
	add_child(prompt)
	title_card = _label(44)
	title_card.anchor_right = 1.0
	title_card.anchor_bottom = 1.0
	title_card.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title_card.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	title_card.add_theme_color_override("font_color", CREAM)
	title_card.add_theme_color_override("font_outline_color", INK)
	title_card.add_theme_constant_override("outline_size", 10)
	add_child(title_card)
	wipe = ColorRect.new()
	wipe.anchor_right = 1.0
	wipe.anchor_bottom = 1.0
	wipe.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sm := ShaderMaterial.new()
	sm.shader = load("res://shaders/ink_wipe.gdshader")
	wipe.material = sm
	add_child(wipe)


func _panel(fill: Color) -> PanelContainer:
	var p := PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = fill
	sb.border_color = INK
	sb.set_border_width_all(3)
	sb.set_content_margin_all(12)
	sb.corner_radius_top_left = 2
	sb.shadow_color = Color(0, 0, 0, 0.25)
	sb.shadow_offset = Vector2(4, 4)
	p.add_theme_stylebox_override("panel", sb)
	return p


func _label(size: int) -> Label:
	var l := Label.new()
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", INK)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.custom_minimum_size = Vector2(420, 0)
	return l


## Show a beat: caption box top-left, balloons stacked bottom-right; holds for a reading time.
func show_beat(beat: Dictionary) -> void:
	_queue.append(beat)
	if not _busy:
		_next()


func _next() -> void:
	if _queue.is_empty():
		_busy = false
		return
	_busy = true
	var beat: Dictionary = _queue.pop_front()
	for c in balloons.get_children():
		c.queue_free()
	var cap: String = beat.get("caption", "")
	caption_box.visible = cap != ""
	caption_label.text = cap.to_upper()
	var words := cap.split(" ").size()
	for d in beat.get("dialogue", []):
		var b := _panel(Color(1, 1, 1))
		var v := VBoxContainer.new()
		var who := _label(13)
		who.text = String(d.get("speaker", "")).to_upper()
		who.add_theme_color_override("font_color", Color(0.65, 0.18, 0.15))
		var t := _label(20)
		t.text = String(d.get("text", "")).to_upper()
		t.custom_minimum_size = Vector2(380, 0)
		v.add_child(who)
		v.add_child(t)
		b.add_child(v)
		balloons.add_child(b)
		words += String(d.get("text", "")).split(" ").size()
	var hold := clampf(2.5 + words * 0.32, 3.0, 9.0)
	var tw := create_tween()
	caption_box.modulate.a = 0.0
	balloons.modulate.a = 0.0
	tw.tween_property(caption_box, "modulate:a", 1.0, 0.25)
	tw.parallel().tween_property(balloons, "modulate:a", 1.0, 0.35)
	tw.tween_interval(hold)
	tw.tween_property(caption_box, "modulate:a", 0.0, 0.4)
	tw.parallel().tween_property(balloons, "modulate:a", 0.0, 0.4)
	tw.tween_callback(_next)


func set_prompt(text: String) -> void:
	prompt.text = text


func show_title(text: String, secs := 2.5) -> void:
	title_card.text = text
	title_card.modulate.a = 1.0
	var tw := create_tween()
	tw.tween_interval(secs)
	tw.tween_property(title_card, "modulate:a", 0.0, 0.8)


## Ink wipe: flood (0 -> 1), call `mid` while the screen is black, then drain (1 -> 0).
func ink_wipe(mid: Callable) -> void:
	var sm: ShaderMaterial = wipe.material
	var tw := create_tween()
	tw.tween_method(func(v): sm.set_shader_parameter("progress", v), 0.0, 1.0, 0.7)
	tw.tween_callback(mid)
	tw.tween_interval(0.25)
	tw.tween_method(func(v): sm.set_shader_parameter("progress", v), 1.0, 0.0, 0.7)
