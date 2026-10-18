// Flat banded inked sky with outlined noise clouds (colours come from world.json).
shader_type sky;
uniform vec3 top : source_color = vec3(0.6, 0.74, 0.76);
uniform vec3 horizon : source_color = vec3(0.93, 0.89, 0.76);
uniform vec3 cloud : source_color = vec3(0.98, 0.96, 0.89);
uniform vec3 below : source_color = vec3(0.3, 0.4, 0.42);

float hash(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
float vnoise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
}

void sky() {
	float z = EYEDIR.y;
	float band = step(0.12, z + vnoise(EYEDIR.xz * 4.0) * 0.04) * 0.5 + step(0.32, z) * 0.5;
	vec3 c = mix(horizon, top, band);
	vec2 uv = EYEDIR.xz / (max(z, 0.0) + 0.08) * 0.6;
	float n = vnoise(uv) * 0.6 + vnoise(uv * 2.3) * 0.3;
	float fade = smoothstep(0.02, 0.12, z);
	c = mix(c, cloud, step(0.58, n * fade));
	c = mix(c, vec3(0.05), step(abs(n * fade - 0.58), 0.006) * fade);
	c = mix(c, below, step(z, -0.002));
	COLOR = c;
}
