import streamlit as st
import requests
import json
import random

st.set_page_config(
    page_title="AI Character Generator",
    page_icon="🎮",
    layout="centered",
)

st.markdown("""
<style>
    .block-container { max-width: 700px; padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)

st.title("🎮 AI Character Generator")
st.caption("Pick gender + body type → AI generates everything → AutoSprite → Godot-ready")

st.divider()

# ── API Keys — loaded from secrets only ──────────────────────────────────────
groq_key = st.secrets["GROQ_API_KEY"]
autosprite_key = st.secrets["AUTOSPRITE_API_KEY"]

st.divider()

# ── Step 1: Gender ─────────────────────────────────────────────────────────────
st.subheader("1️⃣ Gender")
gender = st.radio("Select gender", ["Male", "Female", "Non-binary / Androgynous"],
                  horizontal=True, label_visibility="collapsed")

st.divider()

# ── Step 2: Body Type ─────────────────────────────────────────────────────────
st.subheader("2️⃣ Body Type")

body_types = {
    "Slim":     "Lean and light",
    "Athletic": "Fit and balanced",
    "Stocky":   "Short and strong",
    "Hulking":  "Massive and powerful",
    "Petite":   "Small and compact",
    "Curvy":    "Full-figured",
}

if "body_type" not in st.session_state:
    st.session_state.body_type = None

cols = st.columns(3)
for i, (btype, desc) in enumerate(body_types.items()):
    with cols[i % 3]:
        selected = st.session_state.body_type == btype
        if st.button(f"{'✅ ' if selected else ''}{btype} — {desc}", key=f"bt_{btype}", use_container_width=True):
            st.session_state.body_type = btype
            st.rerun()

if st.session_state.body_type:
    st.success(f"Selected: **{st.session_state.body_type}**")

st.divider()

# ── Generate ──────────────────────────────────────────────────────────────────
ready = bool(st.session_state.body_type)

if not st.session_state.body_type:
    st.warning("Pick a body type to continue.")

if st.button("⚡ Generate Character", type="primary", use_container_width=True, disabled=not ready):
    seed = random.randint(10000, 99999)
    gender_val = gender
    body_val = st.session_state.body_type

    with st.status("🤖 AI is designing your character...", expanded=True) as status:

        # ── Stage 1: AI ───────────────────────────────────────────────────────
        st.write("Crafting character concept...")

        system_prompt = """You are an expert 2D game character designer.
Given only a gender and body type, invent a complete, vivid, original game character.
You decide everything: species, backstory, outfit, art style, color palette, personality, weapon.
Make them unique and interesting — not generic.

Respond ONLY with valid JSON (no markdown fences, no explanation):
{
  "character_name": "string",
  "species": "string",
  "art_style": "string",
  "outfit": "string",
  "color_palette": "string",
  "personality": "string",
  "weapon_or_item": "string",
  "backstory": "string (2 sentences)",
  "autosprite_prompt": "string (rich visual description for 2D game spritesheet, 3-4 sentences)",
  "css_character": "string (complete self-contained HTML page: dark background, CSS character silhouette ~200px tall using divs/border-radius/transforms, idle breathing @keyframes animation)"
}"""

        user_msg = f"Gender: {gender_val}\nBody type: {body_val}\nSeed: {seed}\n\nCreate a unique and compelling game character."

        try:
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_msg},
                    ],
                    "temperature": 1.0,
                    "max_tokens": 3000,
                },
                timeout=40,
            )
            raw = resp.json()["choices"][0]["message"]["content"]

            clean = raw.strip()
            if "```" in clean:
                for part in clean.split("```"):
                    part = part.strip().lstrip("json").strip()
                    try:
                        data = json.loads(part)
                        break
                    except:
                        continue
            else:
                data = json.loads(clean)

            st.write(f"✅ Character created: **{data['character_name']}**")

        except Exception as e:
            status.update(label="❌ AI generation failed", state="error")
            st.error(f"Error: {e}")
            st.code(raw if 'raw' in locals() else "No response")
            st.stop()

        # ── Stage 2: AutoSprite ───────────────────────────────────────────────
        autosprite_result = None
        char_id = "PASTE_YOUR_AUTOSPRITE_ID"

        if autosprite_key:
            st.write("🎯 Sending to AutoSprite...")
            try:
                as_resp = requests.post(
                    "https://autosprite.io/api/characters",
                    headers={
                        "Authorization": f"Bearer {autosprite_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "prompt": data["autosprite_prompt"],
                        "name": data["character_name"],
                        "animations": ["idle", "walk", "run", "jump", "attack"],
                        "sprite_size": 64,
                        "fps": 8,
                    },
                    timeout=30,
                )
                autosprite_result = as_resp.json()
                char_id = autosprite_result.get("id") or autosprite_result.get("character_id", char_id)
                st.write(f"✅ AutoSprite queued — ID: `{char_id}`")
            except Exception as e:
                st.write(f"⚠️ AutoSprite error: {e}")
        else:
            st.write("⚠️ No AutoSprite key — skipping")

        # ── Stage 3: GDScript ─────────────────────────────────────────────────
        st.write("🎮 Building Godot GDScript...")
        class_name = "".join(w.capitalize() for w in data["character_name"].replace("-", " ").split())
        animations = ["idle", "walk", "run", "jump", "attack"]

        anim_entries = "\n".join([
            f'        "{a}": load("res://characters/{class_name}/{a}.png"),'
            for a in animations
        ])
        anim_match = "\n".join([
            f'\t\t"{a}":\n\t\t\tsprite.texture = animations["{a}"]'
            for a in animations
        ])

        gdscript = f'''extends CharacterBody2D
# ────────────────────────────────────────────
# {data["character_name"]} — {data["species"]}
# {data["personality"]} | {data["outfit"]}
# AutoSprite ID: {char_id}
# Seed: {seed}
# ────────────────────────────────────────────

const SPEED = 200.0
const JUMP_VELOCITY = -400.0

@onready var sprite = $AnimatedSprite2D

var current_animation = "idle"
var animations = {{
{anim_entries}
}}

func _ready():
    _play("idle")

func _physics_process(delta):
    if not is_on_floor():
        velocity += get_gravity() * delta

    if Input.is_action_just_pressed("ui_accept") and is_on_floor():
        velocity.y = JUMP_VELOCITY
        _play("jump")

    var dir = Input.get_axis("ui_left", "ui_right")
    if dir != 0:
        velocity.x = dir * SPEED
        sprite.flip_h = dir < 0
        if is_on_floor(): _play("walk")
    else:
        velocity.x = move_toward(velocity.x, 0, SPEED)
        if is_on_floor() and current_animation == "walk":
            _play("idle")

    move_and_slide()

func _play(anim: String):
    if anim == current_animation: return
    current_animation = anim
    if anim in animations:
        match anim:
{anim_match}
        sprite.play()

func attack():
    _play("attack")
    await get_tree().create_timer(0.5).timeout
    _play("idle")
'''
        st.write("✅ GDScript ready")
        status.update(label="✅ All done!", state="complete", expanded=False)

    # ── Results ───────────────────────────────────────────────────────────────
    st.divider()
    st.markdown(f"## 🎭 {data['character_name']}")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Species:** {data['species']}")
        st.markdown(f"**Art Style:** {data['art_style']}")
        st.markdown(f"**Outfit:** {data['outfit']}")
        st.markdown(f"**Color Palette:** {data['color_palette']}")
    with col2:
        st.markdown(f"**Personality:** {data['personality']}")
        st.markdown(f"**Weapon/Item:** {data['weapon_or_item']}")
        st.markdown(f"**Gender:** {gender_val} · **Build:** {body_val}")
        st.markdown(f"**Seed:** `{seed}`")

    st.markdown(f"*{data['backstory']}*")
    st.divider()

    # CSS Preview
    st.subheader("🖼️ CSS Character Preview")
    st.components.v1.html(data["css_character"], height=320, scrolling=False)
    st.divider()

    # AutoSprite Prompt
    st.subheader("📋 AutoSprite Prompt")
    st.code(data["autosprite_prompt"], language=None)

    if autosprite_result:
        sprite_url = autosprite_result.get("sprite_url") or autosprite_result.get("url", "")
        atlas_url  = autosprite_result.get("atlas_url")  or autosprite_result.get("json_url", "")
        if sprite_url:
            st.image(sprite_url, caption="Generated Spritesheet")
            st.download_button("⬇️ Download Spritesheet PNG",
                               requests.get(sprite_url).content,
                               file_name=f"{class_name}_spritesheet.png", mime="image/png")
        if atlas_url:
            st.download_button("⬇️ Download Atlas JSON",
                               requests.get(atlas_url).text,
                               file_name=f"{class_name}_atlas.json", mime="application/json")
        with st.expander("Raw AutoSprite response"):
            st.json(autosprite_result)
    else:
        st.info("No AutoSprite key provided — copy the prompt above and submit at [autosprite.io](https://autosprite.io)")

    st.divider()

    # Godot
    st.subheader("🎮 Godot GDScript")
    st.code(gdscript, language="gdscript")
    st.download_button(
        f"⬇️ Download {class_name}.gd",
        data=gdscript,
        file_name=f"{class_name}.gd",
        mime="text/plain",
        use_container_width=True,
    )
    st.markdown(f"""
**Drop into your Godot project:**
```
res://characters/{class_name}/
    idle.png  walk.png  run.png  jump.png  attack.png  atlas.json
```
Attach `{class_name}.gd` to a `CharacterBody2D` node. Done.
""")
