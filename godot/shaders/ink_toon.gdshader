// Ink cel shading, computed here instead of by Godot's light pipeline (imported glTF lamp
// energies are unusable and fight a toon light()): three flat bands from a key direction,
// shadows = a darker, muted, tinted version of the same hue -- the Blender ink pass's rule.
// Vertex COLOR carries the ink palette baked by tools/build_world.py; COLOR.a < 0.5 = unlit face.
shader_type spatial;
render_mode unshaded, cull_back;

uniform vec3 key_dir = vec3(-0.4, -0.8, -0.4);           // direction light travels (world)
uniform vec3 light_tint = vec3(1.0);            // already linear (world.json)
uniform vec3 shadow_tint = vec3(0.70, 0.74, 0.86);
uniform float shadow_value = 0.58;                         // shadow brightness vs lit
uniform float band_hi = 0.35;
uniform float band_lo = -0.15;
uniform bool debug_albedo = false;
varying vec4 vcol;
varying vec3 wnormal;

void vertex() {
	vcol = COLOR;
	wnormal = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	vec3 base = vcol.rgb;
	if (vcol.a < 0.5 || debug_albedo) {
		ALBEDO = base;
	} else {
		float ndl = dot(normalize(wnormal), -normalize(key_dir));
		float band = ndl > band_hi ? 1.0 : (ndl > band_lo ? 0.5 : 0.0);
		// tints are mood colours: keep their hue, normalise brightness so night stays readable
		vec3 lt = light_tint / max(max(light_tint.r, light_tint.g), max(light_tint.b, 0.001));
		vec3 st = shadow_tint / max(max(shadow_tint.r, shadow_tint.g), max(shadow_tint.b, 0.001));
		vec3 lit = base * mix(vec3(1.0), lt, 0.5);
		// shadow: same hue, darker, a little desaturated and pulled toward the tint
		float g = dot(base, vec3(0.299, 0.587, 0.114));
		vec3 sh = mix(base, vec3(g), 0.2) * mix(vec3(1.0), st, 0.6) * shadow_value;
		ALBEDO = mix(sh, lit, band);
	}
}
