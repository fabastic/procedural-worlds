// Ink-blot wipe between scenes: progress 0 -> 1 floods the screen with a jagged ink blot.
shader_type canvas_item;
uniform float progress : hint_range(0.0, 1.0) = 0.0;
uniform vec3 ink = vec3(0.03, 0.025, 0.02);

float hash(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
float vnoise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
}

void fragment() {
	vec2 p = UV - vec2(0.62, 0.45);
	p.x *= 1.78;
	float n = vnoise(UV * 7.0) * 0.18 + vnoise(UV * 23.0) * 0.06;
	float blot = step(length(p) + n, progress * 1.5);
	COLOR = vec4(ink, blot);
}
