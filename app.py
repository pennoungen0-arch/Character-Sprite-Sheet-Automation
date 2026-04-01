import streamlit as st
import requests
import json
import random
import time
from pathlib import Path

# ─── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Character Pipeline",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .pipeline-step {
        background: #1e1e2e;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .step-active {
        border-color: #7c3aed;
        box-shadow: 0 0 10px rgba(124, 58, 237, 0.3);
    }
    .tag-chip {
        display: inline-block;
        background: #2d2d44;
        border: 1px solid #444;
        border-radius: 20px;
        padding: 4px 12px;
        margin: 3px;
        font-size: 13px;
        cursor: pointer;
    }
    .stButton > button {
        width: 100%;
        border-radius: 8px;
    }
    .output-box {
        background: #0d1117;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 1rem;
        font-family: monospace;
        font-size: 12px;
        overflow-x: auto;
    }
    .success-badge {
        background: #065f46;
        color: #34d399;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ─── Trait data ────────────────────────────────────────────────────────────────
TRAITS = {
    "Build": ["Slim", "Athletic", "Stocky", "Tiny", "Hulking", "Lanky", "Curvy", "Compact"],
    "Height": ["Very short", "Short", "Average", "Tall", "Very tall", "Chibi-sized"],
    "Species": ["Human", "Elf", "Dwarf", "Robot", "Demon", "Angel", "Orc", "Cat-folk", "Undead", "Fairy"],
    "Art Style": ["Pixel art", "Anime", "Cartoon", "Painterly", "Flat vector", "Retro RPG", "Chibi", "Realistic"],
    "Outfit": ["Fantasy warrior", "Sci-fi suit", "Casual streetwear", "Mage robe", "Ninja", "Steampunk", "Royal armor", "Rogue leather"],
    "Color Palette": ["Warm earthy", "Cool blue/silver", "Vibrant neon", "Pastel soft", "Dark gothic", "Forest green", "Fire red/gold", "Monochrome"],
    "Personality": ["Brave", "Mysterious", "Cheerful", "Grim", "Wise", "Chaotic", "Calm", "Wild"],
    "Weapon/Item": ["Sword", "Staff", "Bow", "Daggers", "Axe", "Tome", "Unarmed", "Scythe"],
}

# ─── Session state init ────────────────────────────────────────────────────────
if "selected_traits" not in st.session_state:
    st.session_state.selected_traits = {k: None for k in TRAITS}
if "seed" not in st.session_state:
    st.session_state.seed = random.randint(10000, 99999)
if "generated_prompt" not in st.session_state:
    st.session_state.generated_prompt = None
if "css_preview" not in st.session_state:
    st.session_state.css_preview = None
if "autosprite_result" not in st.session_state:
    st.session_state.autosprite_result = None
if "gdscript" not in st.session_state:
    st.session_state.gdscript = None
if "pipeline_stage" not in st.session_state:
    st.session_state.pipeline_stage = 0

# ─── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1 style="color:white; margin:0; font-size:2.2rem;">🎮 AI Character Pipeline</h1>
    <p style="color:#a0aec0; margin:0.5rem 0 0 0;">Groq / Qwen → CSS Preview → AutoSprite → Godot-ready export</p>
</div>
""", unsafe_allow_html=True)

# Pipeline progress
stages = ["⚙️ Setup", "🎨 Traits", "🤖 AI Prompt", "🖼️ CSS Preview", "🎯 AutoSprite", "🎮 Godot Export"]
cols = st.columns(len(stages))
for i, (col, stage) in enumerate(zip(cols, stages)):
    with col:
        if i <= st.session_state.pipeline_stage:
            st.markdown(f"**{stage}**")
        else:
            st.markdown(f"<span style='color:#555'>{stage}</span>", unsafe_allow_html=True)

st.divider()

# ─── Sidebar: Setup ────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Setup")

    ai_model = st.radio("AI Model", ["Groq · Llama 3.3 70B", "Qwen 2.5 72B · OpenRouter"], index=0)

    groq_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...")
    autosprite_key = st.text_input("AutoSprite API Key", type="password", placeholder="as_...")

    if "Qwen" in ai_model:
        qwen_key = st.text_input("OpenRouter API Key", type="password", placeholder="sk-or-...")
    else:
        qwen_key = ""

    st.divider()
    st.subheader("🎮 Godot Export Settings")
    sprite_size = st.selectbox("Sprite size (px)", [16, 32, 48, 64, 128], index=3)
    animations_raw = st.text_input("Animations", value="idle,walk,run,jump,attack")
    fps = st.number_input("FPS", min_value=4, max_value=60, value=8)
    animations = [a.strip() for a in animations_raw.split(",") if a.strip()]

    st.divider()
    seed_col, btn_col = st.columns([3, 1])
    with seed_col:
        seed = st.number_input("Seed", value=st.session_state.seed, min_value=0, max_value=999999, step=1)
        st.session_state.seed = seed
    with btn_col:
        st.write("")
        st.write("")
        if st.button("🎲"):
            st.session_state.seed = random.randint(10000, 99999)
            st.rerun()

# ─── Main tabs ─────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🎨 Traits & Generate", "🖼️ Preview & AutoSprite", "🎮 Godot Export"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Traits & Generate
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Character Traits")
    st.caption("Pick traits or leave blank for full random generation")

    # Randomize all button
    rcol1, rcol2 = st.columns([3, 1])
    with rcol2:
        if st.button("🎲 Randomize All Traits"):
            random.seed(st.session_state.seed)
            for k in TRAITS:
                st.session_state.selected_traits[k] = random.choice(TRAITS[k])
            st.rerun()
    with rcol1:
        if st.button("🗑️ Clear All Traits"):
            st.session_state.selected_traits = {k: None for k in TRAITS}
            st.rerun()

    # Trait grid — 2 columns
    trait_keys = list(TRAITS.keys())
    left_traits = trait_keys[:4]
    right_traits = trait_keys[4:]

    col_l, col_r = st.columns(2)

    def render_trait_group(col, keys):
        with col:
            for trait_name in keys:
                st.markdown(f"**{trait_name}**")
                options = [None] + TRAITS[trait_name]
                labels = ["(random)"] + TRAITS[trait_name]
                current = st.session_state.selected_traits.get(trait_name)
                current_idx = options.index(current) if current in options else 0
                selected = st.selectbox(
                    trait_name,
                    options=options,
                    format_func=lambda x: "(random)" if x is None else x,
                    index=current_idx,
                    key=f"trait_{trait_name}",
                    label_visibility="collapsed",
                )
                st.session_state.selected_traits[trait_name] = selected

    render_trait_group(col_l, left_traits)
    render_trait_group(col_r, right_traits)

    st.divider()

    # Current trait summary
    pinned = {k: v for k, v in st.session_state.selected_traits.items() if v}
    if pinned:
        st.markdown("**Pinned traits:** " + " · ".join([f"`{k}: {v}`" for k, v in pinned.items()]))
    else:
        st.info("No traits pinned — AI will fully randomize the character.")

    st.divider()
    st.subheader("🤖 Generate AI Prompt")

    if st.button("✨ Generate Character Prompt", type="primary", use_container_width=True):
        api_key = groq_key if "Groq" in ai_model else qwen_key
        if not api_key:
            st.error("Please enter your API key in the sidebar.")
        else:
            with st.spinner("AI is crafting your character..."):
                random.seed(st.session_state.seed)

                # Build trait context
                trait_lines = []
                for k, v in TRAITS.items():
                    val = st.session_state.selected_traits.get(k) or random.choice(v)
                    trait_lines.append(f"- {k}: {val}")

                trait_context = "\n".join(trait_lines)

                system_prompt = """You are an expert game character designer. 
Given character traits, write a rich AutoSprite-compatible character description 
for a 2D game spritesheet. Be vivid, specific, and visual. 
Then write a matching CSS silhouette representation using pure CSS shapes.
Format your response as JSON with keys: 
  "character_name", "prompt" (for AutoSprite), "description", "css_code" (complete HTML+CSS for preview), "traits_used"
Return ONLY valid JSON, no markdown."""

                user_msg = f"""Generate a game character with these traits:
{trait_context}

Seed: {st.session_state.seed}

For css_code: Create a full HTML page with a centered CSS character silhouette 
(use divs, border-radius, transforms to make a recognizable character shape). 
Include idle breathing animation. Dark background. Character should be ~200px tall."""

                try:
                    if "Groq" in ai_model:
                        resp = requests.post(
                            "https://api.groq.com/openai/v1/chat/completions",
                            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                            json={
                                "model": "llama-3.3-70b-versatile",
                                "messages": [
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": user_msg}
                                ],
                                "temperature": 0.9,
                                "max_tokens": 2000,
                            },
                            timeout=30
                        )
                        raw = resp.json()["choices"][0]["message"]["content"]
                    else:
                        resp = requests.post(
                            "https://openrouter.ai/api/v1/chat/completions",
                            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                            json={
                                "model": "qwen/qwen-2.5-72b-instruct",
                                "messages": [
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": user_msg}
                                ],
                                "temperature": 0.9,
                                "max_tokens": 2000,
                            },
                            timeout=30
                        )
                        raw = resp.json()["choices"][0]["message"]["content"]

                    # Parse JSON
                    clean = raw.strip()
                    if clean.startswith("```"):
                        clean = clean.split("```")[1]
                        if clean.startswith("json"):
                            clean = clean[4:]
                    clean = clean.strip().rstrip("```").strip()

                    data = json.loads(clean)
                    st.session_state.generated_prompt = data
                    st.session_state.css_preview = data.get("css_code", "")
                    st.session_state.pipeline_stage = max(st.session_state.pipeline_stage, 2)
                    st.success(f"✅ Character generated: **{data.get('character_name', 'Unknown')}**")

                except Exception as e:
                    st.error(f"Generation failed: {e}")
                    st.code(raw if 'raw' in locals() else str(e))

    # Show prompt result
    if st.session_state.generated_prompt:
        d = st.session_state.generated_prompt
        st.success(f"### {d.get('character_name', 'Character')}")
        st.markdown(f"*{d.get('description', '')}*")

        with st.expander("📋 AutoSprite Prompt (copy this)"):
            st.code(d.get("prompt", ""), language=None)

        with st.expander("🧬 Traits Used"):
            for k, v in (d.get("traits_used") or {}).items():
                st.markdown(f"- **{k}**: {v}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Preview & AutoSprite
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    col_preview, col_sprite = st.columns(2)

    with col_preview:
        st.subheader("🖼️ CSS Character Preview")
        if st.session_state.css_preview:
            st.components.v1.html(st.session_state.css_preview, height=350, scrolling=False)
            st.session_state.pipeline_stage = max(st.session_state.pipeline_stage, 3)
        else:
            st.info("Generate a character first in the Traits tab.")

    with col_sprite:
        st.subheader("🎯 AutoSprite Submission")
        if not st.session_state.generated_prompt:
            st.info("Generate a character prompt first.")
        else:
            prompt_text = st.session_state.generated_prompt.get("prompt", "")
            char_name = st.session_state.generated_prompt.get("character_name", "character")

            st.markdown("**Prompt to send:**")
            edited_prompt = st.text_area("AutoSprite Prompt", value=prompt_text, height=150, key="autosprite_prompt_edit")

            queue_sprite = st.checkbox("Auto-queue spritesheet job (Walk + Idle)", value=True)

            if st.button("🚀 Send to AutoSprite", type="primary", use_container_width=True):
                if not autosprite_key:
                    st.error("Enter your AutoSprite API key in the sidebar.")
                else:
                    with st.spinner("Sending to AutoSprite..."):
                        try:
                            payload = {
                                "prompt": edited_prompt,
                                "name": char_name,
                                "animations": animations if queue_sprite else ["idle"],
                                "sprite_size": sprite_size,
                                "fps": fps,
                            }
                            resp = requests.post(
                                "https://autosprite.io/api/characters",
                                headers={
                                    "Authorization": f"Bearer {autosprite_key}",
                                    "Content-Type": "application/json"
                                },
                                json=payload,
                                timeout=30
                            )
                            result = resp.json()
                            st.session_state.autosprite_result = result
                            st.session_state.pipeline_stage = max(st.session_state.pipeline_stage, 4)
                            st.success("✅ Sent to AutoSprite!")
                        except Exception as e:
                            st.error(f"AutoSprite error: {e}")

            if st.session_state.autosprite_result:
                res = st.session_state.autosprite_result
                st.divider()
                st.markdown("**AutoSprite Response:**")

                char_id = res.get("id") or res.get("character_id", "")
                if char_id:
                    st.markdown(f"**Character ID:** `{char_id}`")
                    st.markdown(f"🔗 [View in AutoSprite Dashboard](https://autosprite.io/dashboard)")

                sprite_url = res.get("sprite_url") or res.get("url", "")
                if sprite_url:
                    st.image(sprite_url, caption="Generated Spritesheet")
                    st.download_button(
                        "⬇️ Download Spritesheet PNG",
                        data=requests.get(sprite_url).content,
                        file_name=f"{char_name}_spritesheet.png",
                        mime="image/png"
                    )

                atlas_url = res.get("atlas_url") or res.get("json_url", "")
                if atlas_url:
                    atlas_data = requests.get(atlas_url).text
                    st.download_button(
                        "⬇️ Download Atlas JSON",
                        data=atlas_data,
                        file_name=f"{char_name}_atlas.json",
                        mime="application/json"
                    )

                with st.expander("Raw AutoSprite Response"):
                    st.json(res)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Godot Export
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("🎮 Godot GDScript Export")

    if not st.session_state.generated_prompt:
        st.info("Generate a character first to get the Godot export.")
    else:
        char_name = st.session_state.generated_prompt.get("character_name", "Character")
        char_id = ""
        if st.session_state.autosprite_result:
            char_id = st.session_state.autosprite_result.get("id") or st.session_state.autosprite_result.get("character_id", "")

        # Build safe class name
        class_name = "".join(w.capitalize() for w in char_name.replace("-", " ").split())

        # Build animation dict
        anim_entries = []
        for anim in animations:
            anim_entries.append(f'        "{anim}": load("res://characters/{class_name}/{anim}.png"),')
        anim_block = "\n".join(anim_entries)

        anim_match = []
        for anim in animations:
            anim_match.append(f'\t\t"{anim}":\n\t\t\tsprite.texture = animations["{anim}"]')
        anim_match_block = "\n".join(anim_match)

        gdscript = f'''extends CharacterBody2D
# ─────────────────────────────────────────────────────
# Character: {char_name}
# AutoSprite ID: {char_id or "PASTE_YOUR_ID_HERE"}
# Generated by AI Character Pipeline
# Seed: {st.session_state.seed}
# Sprite size: {sprite_size}px  |  FPS: {fps}
# ─────────────────────────────────────────────────────

const SPEED = 200.0
const JUMP_VELOCITY = -400.0

@onready var sprite = $AnimatedSprite2D
@onready var animation_player = $AnimationPlayer

var current_animation = "idle"

var animations = {{
{anim_block}
}}

func _ready():
    _play_animation("idle")

func _physics_process(delta):
    # Gravity
    if not is_on_floor():
        velocity += get_gravity() * delta

    # Jump
    if Input.is_action_just_pressed("ui_accept") and is_on_floor():
        velocity.y = JUMP_VELOCITY
        _play_animation("jump")

    # Horizontal movement
    var direction = Input.get_axis("ui_left", "ui_right")
    if direction != 0:
        velocity.x = direction * SPEED
        sprite.flip_h = direction < 0
        if is_on_floor():
            _play_animation("walk")
    else:
        velocity.x = move_toward(velocity.x, 0, SPEED)
        if is_on_floor() and current_animation == "walk":
            _play_animation("idle")

    move_and_slide()

func _play_animation(anim_name: String):
    if anim_name == current_animation:
        return
    if anim_name in animations:
        current_animation = anim_name
        match anim_name:
{anim_match_block}
        sprite.play()

func attack():
    _play_animation("attack")
    await get_tree().create_timer(0.5).timeout
    _play_animation("idle")
'''

        st.session_state.gdscript = gdscript
        st.session_state.pipeline_stage = max(st.session_state.pipeline_stage, 5)

        st.code(gdscript, language="gdscript")

        st.download_button(
            f"⬇️ Download {class_name}.gd",
            data=gdscript,
            file_name=f"{class_name}.gd",
            mime="text/plain",
            use_container_width=True,
        )

        st.divider()
        st.subheader("📁 Godot Project Setup Guide")

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"""
**Folder structure:**
```
res://
└── characters/
    └── {class_name}/
        ├── idle.png
        ├── walk.png
        ├── run.png
        ├── jump.png
        ├── attack.png
        └── atlas.json
```
""")
        with col_b:
            st.markdown(f"""
**Scene setup:**
1. Create `CharacterBody2D` node
2. Add `AnimatedSprite2D` child
3. Add `CollisionShape2D` child
4. Attach `{class_name}.gd` script
5. Set sprite size to **{sprite_size}x{sprite_size}**
6. Import PNG + JSON atlas from AutoSprite
""")

        if char_id:
            st.success(f"✅ AutoSprite ID `{char_id}` is embedded in the script. Download PNG + JSON atlas from your dashboard and drop into `res://characters/{class_name}/`")
        else:
            st.warning("⚠️ Send to AutoSprite first to embed the character ID automatically.")

# ─── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption("AI Character Pipeline · Groq / Qwen → AutoSprite → Godot · Built with Streamlit")
