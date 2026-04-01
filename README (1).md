# 🎮 AI Character Pipeline

**Groq / Qwen → CSS Preview → AutoSprite → Godot-ready export**

A Streamlit app that generates randomized game characters using AI, previews them as CSS silhouettes, submits them to AutoSprite for spritesheet generation, and exports ready-to-use Godot GDScript.

---

## 🚀 Quick Start (Local)

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open http://localhost:8501

---

## ☁️ Deploy to Streamlit Cloud

1. Push this folder to a GitHub repo
2. Go to https://share.streamlit.io
3. Click **New app** → select your repo → set `app.py` as the main file
4. Add your API keys as **Secrets** (Settings → Secrets):

```toml
# .streamlit/secrets.toml  (DO NOT commit this file)
GROQ_API_KEY = "gsk_..."
AUTOSPRITE_API_KEY = "as_..."
OPENROUTER_API_KEY = "sk-or-..."  # optional, for Qwen
```

---

## 🔑 API Keys

| Service | Where to get it | Cost |
|---|---|---|
| Groq | https://console.groq.com/keys | Free tier |
| AutoSprite | https://autosprite.io/mcp | Sign-in required |
| Qwen (optional) | https://openrouter.ai/keys | Pay-per-use |

---

## 🔄 Pipeline Flow

```
Pick Traits → AI Generates Prompt → CSS Preview → AutoSprite Upload → Spritesheet Job → Godot GDScript
```

### Tabs

| Tab | What it does |
|---|---|
| 🎨 Traits & Generate | Pick character traits, generate AI prompt + CSS preview |
| 🖼️ Preview & AutoSprite | View CSS silhouette, submit to AutoSprite, download spritesheet |
| 🎮 Godot Export | Download ready-to-use GDScript + setup guide |

---

## 🎮 Godot Integration

1. Download the generated `.gd` script from the Godot Export tab
2. Get your PNG spritesheet + JSON atlas from your AutoSprite dashboard
3. Drop files into `res://characters/YourCharacter/`
4. Create a `CharacterBody2D` scene, attach the script

The script comes pre-wired with:
- Movement (walk, run, jump)
- All animations from your settings
- `flip_h` for left/right mirroring
- AutoSprite character ID embedded as a comment
