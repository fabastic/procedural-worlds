// Flat 3-band cel shading from the ink colours Blender baked into vertex COLOR.
// COLOR.a < 0.5 marks unlit faces (neon, lamps, sky cards, fire): drawn as flat emission.
shader_type spatial;
render_mode cull_back, specular_disabled;

uniform vec3 light_tint : source_color = vec3(1.0);
uniform float band_hi = 0.55;
uniform float band_lo = 0.12;
varying vec4 vcol;

void vertex() {
	vcol = COLOR;
}

void fragment() {
	if (vcol.a < 0.5) {
		ALBEDO = vec3(0.0);
		EMISSION = vcol.rgb;
	} else {
		ALBEDO = vcol.rgb;
	}
	ROUGHNESS = 1.0;
}

void light() {
	float ndl = clamp(dot(NORMAL, LIGHT), 0.0, 1.0) * ATTENUATION;
	float band = ndl > band_hi ? 1.0 : (ndl > band_lo ? 0.55 : 0.0);
	DIFFUSE_LIGHT += LIGHT_COLOR / PI * band * light_tint;
}
