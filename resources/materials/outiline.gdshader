shader_type canvas_item;

uniform vec4 outline_color : source_color = vec4(0.0, 0.0, 0.0, 1.0);
uniform float outline_width : hint_range(0.0, 4.0) = 1.0;

void fragment() {
	vec2 size = TEXTURE_PIXEL_SIZE * outline_width;
	vec4 col = texture(TEXTURE, UV);

	if (col.a < 0.5) {
		// Nur deckende Nachbarn zaehlen - Halbdurchsichtiges wie der
		// Schwungbogen bekommt keinen Rand.
		float alpha = 0.0;
		alpha += step(0.5, texture(TEXTURE, UV + vec2(size.x, 0.0)).a);
		alpha += step(0.5, texture(TEXTURE, UV + vec2(-size.x, 0.0)).a);
		alpha += step(0.5, texture(TEXTURE, UV + vec2(0.0, size.y)).a);
		alpha += step(0.5, texture(TEXTURE, UV + vec2(0.0, -size.y)).a);
		alpha += step(0.5, texture(TEXTURE, UV + vec2(size.x, size.y)).a);
		alpha += step(0.5, texture(TEXTURE, UV + vec2(-size.x, -size.y)).a);
		alpha += step(0.5, texture(TEXTURE, UV + vec2(size.x, -size.y)).a);
		alpha += step(0.5, texture(TEXTURE, UV + vec2(-size.x, size.y)).a);

		if (alpha > 0.0) {
			col = vec4(outline_color.rgb, 1.0);
		}
	}

	COLOR = col;
}