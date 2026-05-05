# Shared Image Constraints

Apply these constraints strictly to every image generation (`Build`, `Refresh`, `Scene-Merge`).

## Identity (Critical)

- The character MUST remain the same.
- Face, hair, skin tone, and body proportions MUST stay consistent.
- Do NOT change identity, age, ethnicity, or facial structure.
- Do NOT introduce a different person.

## Visual Style

- Output MUST be photorealistic.
- Keep rendering style consistent across images.
- Do NOT use stylized, anime, or illustrative styles unless explicitly required by scene context.

## Clean Output

- No text, captions, logos, watermarks, or UI elements.
- No borders, overlays, or visual artifacts.

## Perspective

- Follow the perspective defined by the scene.
- Use first-person ONLY if explicitly required.

If first-person:
- The viewer must be completely invisible.
- No body parts, shadows, or reflections visible.

## Conflict Handling

If instructions conflict, resolve in this order:
1. Identity
2. Scene context
3. Visual consistency
4. Style