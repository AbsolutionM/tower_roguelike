shader_type canvas_item;
render_mode unshaded;

// Umriss fuer eine CanvasGroup: Figur, Haende und Waffe werden erst
// gemeinsam in den Backbuffer gezeichnet, dann laeuft der Rand um die
// gemeinsame Silhouette - nicht um jedes Teil einzeln.
//
// Godot zeichnet Gruppenkinder in den Backbuffer; ein eigenes Material muss
// ihn ueber screen_texture lesen (Alpha ist dort vormultipliziert).
uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_nearest;
uniform vec4 outline_color : source_color = vec4(0.0, 0.0, 0.0, 1.0);
// In Bildschirmpixeln. Die Figur hat 3 Bildschirmpixel je Texturpixel.
uniform float outline_width : hint_range(0.0, 8.0) = 3.0;

float solid(vec2 uv) {
	return step(0.5, textureLod(screen_texture, uv, 0.0).a);
}

void fragment() {
	vec4 c = textureLod(screen_texture, SCREEN_UV, 0.0);
	if (c.a > 0.0001) {
		c.rgb /= c.a;
	}

	if (c.a < 0.5) {
		vec2 px = SCREEN_PIXEL_SIZE * outline_width;
		// Nur deckende Nachbarn zaehlen - halbdurchsichtige Effekte wie der
		// Schwungbogen bekommen keinen Rand.
		float alpha = 0.0;
		alpha += solid(SCREEN_UV + vec2(px.x, 0.0));
		alpha += solid(SCREEN_UV + vec2(-px.x, 0.0));
		alpha += solid(SCREEN_UV + vec2(0.0, px.y));
		alpha += solid(SCREEN_UV + vec2(0.0, -px.y));
		alpha += solid(SCREEN_UV + vec2(px.x, px.y));
		alpha += solid(SCREEN_UV + vec2(-px.x, -px.y));
		alpha += solid(SCREEN_UV + vec2(px.x, -px.y));
		alpha += solid(SCREEN_UV + vec2(-px.x, px.y));
		if (alpha > 0.0) {
			c = vec4(outline_color.rgb, 1.0);
		}
	}

	COLOR *= c;
}
