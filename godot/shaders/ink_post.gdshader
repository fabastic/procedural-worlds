// Screen-space ink: wobbly depth+normal edges that boil on twos (6 drawings per second), hatching in
// dark areas, paper tint + grain + mottling and a warm vignette. Drawn by a quad parented to the camera.
shader_type spatial;
render_mode unshaded, depth_test_disabled, depth_draw_never, cull_disabled, fog_disabled;

uniform sampler2D screen_tex : hint_screen_texture, filter_linear_mipmap;
uniform sampler2D depth_tex : hint_depth_texture, filter_nearest;
uniform sampler2D normal_tex : hint_normal_roughness_texture, filter_nearest;
uniform vec3 ink = vec3(0.025, 0.02, 0.018);
uniform vec3 paper = vec3(0.95, 0.91, 0.82);
uniform float line_px = 2.2;
uniform float boil_fps = 6.0;
uniform float hatch = 1.0;
uniform int debug_mode = 0;   // 1 = edges only, 2 = raw screen

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vnoise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
}

float lin_depth(vec2 uv, mat4 inv_proj) {
	float d = texture(depth_tex, uv).r;
	vec4 v = inv_proj * vec4(uv * 2.0 - 1.0, d, 1.0);
	return -v.z / v.w;
}

void vertex() {
	POSITION = vec4(VERTEX.xy * 2.0, 1.0, 1.0);
}

void fragment() {
	vec2 res = VIEWPORT_SIZE;
	float step_t = floor(TIME * boil_fps);
	vec2 wob = (vec2(vnoise(SCREEN_UV * 9.0 + step_t * 1.37), vnoise(SCREEN_UV * 9.0 + 31.0 + step_t * 0.71)) - 0.5) * 3.0 / res;
	vec2 uv = SCREEN_UV + wob;
	float w = line_px * mix(0.6, 1.4, vnoise(SCREEN_UV * 14.0 + step_t * 0.5)) / res.y;
	vec2 o = vec2(w * res.y / res.x, w);
	float dc = lin_depth(uv, INV_PROJECTION_MATRIX);
	float de = 0.0;
	vec3 nc = texture(normal_tex, uv).xyz * 2.0 - 1.0;
	float ne = 0.0;
	for (int i = 0; i < 4; i++) {
		vec2 off = i == 0 ? vec2(o.x, 0.0) : (i == 1 ? vec2(-o.x, 0.0) : (i == 2 ? vec2(0.0, o.y) : vec2(0.0, -o.y)));
		float d = lin_depth(uv + off, INV_PROJECTION_MATRIX);
		de = max(de, abs(d - dc) / max(dc, 0.05));
		vec3 n = texture(normal_tex, uv + off).xyz * 2.0 - 1.0;
		ne = max(ne, 1.0 - dot(nc, n));
	}
	float edge = max(smoothstep(0.04, 0.09, de), smoothstep(0.35, 0.6, ne));
	vec3 col = texture(screen_tex, SCREEN_UV).rgb;
	float lum = dot(col, vec3(0.2126, 0.7152, 0.0722));
	vec2 px = SCREEN_UV * res;
	float stripes = fract((px.x + px.y) / 7.0 + vnoise(px * 0.02 + step_t) * 0.6);
	float breaks = step(0.38, vnoise(px * vec2(0.02, 0.12) + step_t * 0.3));
	float h = hatch * step(stripes, 0.28) * breaks * smoothstep(0.22, 0.08, lum);
	col = mix(col, col * 0.35, h * 0.8);
	col *= mix(vec3(1.0), paper, 0.6);
	col *= mix(0.92, 1.04, hash(floor(px))) * mix(0.94, 1.03, vnoise(SCREEN_UV * 3.0));
	col = mix(col, ink, edge);
	float r = length(SCREEN_UV - 0.5);
	col = mix(col, col * vec3(0.62, 0.52, 0.40), smoothstep(0.45, 0.85, r) * 0.5);
	if (debug_mode == 1) { col = vec3(edge); }
	if (debug_mode == 2) { col = texture(screen_tex, SCREEN_UV).rgb; }
	ALBEDO = col;
}
