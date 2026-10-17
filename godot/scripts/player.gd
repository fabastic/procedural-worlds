## First-person protagonist: pointer-lock mouse look, WASD, sprint, gravity, eye height from the story.
extends CharacterBody3D

@export var speed := 3.2
@export var sprint_mult := 1.8
@export var mouse_sens := 0.0022
@export var eye_height := 1.65

var camera: Camera3D
var _pitch := 0.0
const GRAVITY := 9.8


func _ready() -> void:
	var shape := CollisionShape3D.new()
	var cap := CapsuleShape3D.new()
	cap.radius = 0.28
	cap.height = max(0.9, eye_height + 0.1)
	shape.shape = cap
	shape.position.y = cap.height * 0.5
	add_child(shape)
	camera = Camera3D.new()
	camera.position.y = eye_height
	camera.fov = 70.0
	camera.near = 0.05
	camera.far = 800.0
	add_child(camera)
	camera.make_current()
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		rotate_y(-event.relative.x * mouse_sens)
		_pitch = clamp(_pitch - event.relative.y * mouse_sens, -1.45, 1.45)
		camera.rotation.x = _pitch
	elif event is InputEventMouseButton and event.pressed:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	elif event.is_action_pressed("ui_cancel"):
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE


func _physics_process(delta: float) -> void:
	if not is_on_floor():
		velocity.y -= GRAVITY * delta
	var dir2 := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
	var dir := (transform.basis * Vector3(dir2.x, 0.0, dir2.y)).normalized()
	var s := speed * (sprint_mult if Input.is_action_pressed("sprint") else 1.0)
	velocity.x = dir.x * s
	velocity.z = dir.z * s
	move_and_slide()
	if global_position.y < -50.0:            # fell out of the world: back to the spawn
		get_parent().call("respawn")


func look_at_point(p: Vector3) -> Vector3:
	return (p - camera.global_position).normalized()
