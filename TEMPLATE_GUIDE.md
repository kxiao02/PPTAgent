# Template Creation Guide 🎨

This guide walks you through creating custom PowerPoint templates for PPTAgent. Templates define the visual style, layouts, and structure that PPTAgent uses to generate presentations.

## Table of Contents

- [Template Structure](#template-structure)
- [Quick Start](#quick-start)
- [Step-by-Step Guide](#step-by-step-guide)
  - [1. Design Your Template PPTX](#1-design-your-template-pptx)
  - [2. Create Template Directory](#2-create-template-directory)
  - [3. Generate Template Metadata](#3-generate-template-metadata)
  - [4. Add Description](#4-add-description)
  - [5. Generate Preview Image](#5-generate-preview-image)
- [Template Design Best Practices](#template-design-best-practices)
- [Testing Your Template](#testing-your-template)
- [Troubleshooting](#troubleshooting)

---

## Template Structure

Each PPTAgent template is a directory containing the following files:

```
pptagent/templates/your-template/
├── source.pptx              # [Required] Your PowerPoint template
├── slide_induction.json     # [Auto-generated] Extracted layout schemas
├── image_stats.json         # [Auto-generated] Image analysis metadata
├── description.txt          # [Required] Human-readable description
└── preview.png              # [Auto-generated] First slide preview
```

### File Descriptions

| File | Status | Description |
|------|--------|-------------|
| `source.pptx` | **Required** | The PowerPoint file containing your template slides. Should include examples of all layout types you want to use. |
| `slide_induction.json` | Auto-generated | Contains extracted layout patterns and content schemas. Generated during first use or by running the induction script. |
| `image_stats.json` | Auto-generated | Stores image captions and metadata. Generated during first use. |
| `description.txt` | **Required** | A brief (1-2 sentence) description of the template. Used in the template selector UI. |
| `preview.png` | Auto-generated | Preview image of the first slide. Generated using the preview generation script. |

---

## Quick Start

**TL;DR**: Create a template in 5 commands:

```bash
# 1. Create template directory
mkdir -p pptagent/templates/my-template

# 2. Copy your PPTX file
cp my-template.pptx pptagent/templates/my-template/source.pptx

# 3. Write description
echo "A modern, minimalist template for business presentations." > pptagent/templates/my-template/description.txt

# 4. Generate preview image
./scripts/generate_template_previews.sh

# 5. Test your template (metadata will be auto-generated on first use)
python -c "
from pptagent.mcp_server import PPTAgentServer
server = PPTAgentServer()
server.set_template('my-template')
print('Template loaded successfully!')
"
```

---

## Step-by-Step Guide

### 1. Design Your Template PPTX

Create a PowerPoint file that showcases the layouts and styles you want PPTAgent to use. Follow these **critical design guidelines** from [BESTPRACTICE.md](BESTPRACTICE.md):

#### ✅ Required Slides

Your template **must** include at least:
- **Opening slide** (title/cover page)
- **Ending slide** (thank you/contact page)
- **2-3 content slides** with different layouts (text-heavy, image-heavy, mixed)

Optional but recommended:
- **Table of Contents slide**
- **Section Header slide**

#### ✅ Layout Guidelines

- **Simple layouts**: Each slide should have ≤6 elements
- **Effective spacing**: Leave white space around elements for flexibility
- **Consistent hierarchy**: Group related content in the same element (use bullet points, not multiple text boxes)
- **Text capacity**: Fill text boxes to ~60% capacity to allow PPTAgent to adjust content length

#### ✅ Text Frame Settings

Set all text frames to **"Shrink text on overflow"** in PowerPoint:
1. Right-click text box → Format Shape
2. Text Options → Text Box
3. Select "Shrink text on overflow"

This ensures generated content fits properly regardless of length.

#### ❌ Elements to Avoid

PPTAgent uses `python-pptx` which has limitations. **Avoid these elements**:
- Nested group shapes
- Freeform shapes
- Videos/audio
- SmartArt (use simple shapes instead)
- Complex animations

Slides with these elements will be skipped during analysis.

#### 🎨 Functional Layout Types

PPTAgent recognizes four functional layout types:
1. **Opening**: Title slide / cover page
2. **Table of Contents**: Outline of presentation sections
3. **Section Header**: Divider slides between sections
4. **Ending**: Closing slide / thank you page

Label these slides by naming them appropriately (e.g., "Opening", "TOC", "Section", "Ending") or PPTAgent will infer them from content.

### 2. Create Template Directory

```bash
# Choose a descriptive, lowercase name with hyphens
TEMPLATE_NAME="my-corporate-template"

# Create directory
mkdir -p pptagent/templates/$TEMPLATE_NAME

# Copy your PPTX
cp /path/to/your/template.pptx pptagent/templates/$TEMPLATE_NAME/source.pptx
```

**Naming conventions**:
- Use lowercase letters, numbers, and hyphens
- Be descriptive: `academic-blue`, `startup-pitch`, `conference-2024`
- Avoid spaces and special characters

### 3. Generate Template Metadata

Template metadata (`slide_induction.json` and `image_stats.json`) is **automatically generated** the first time you use a template. However, you can pre-generate it for faster first-time performance:

#### Option A: Auto-generate on first use (Recommended)

Simply use the template. PPTAgent will analyze it automatically:

```python
from pptagent.mcp_server import PPTAgentServer

server = PPTAgentServer()
server.set_template('my-corporate-template')
# Metadata files will be created during initialization
```

#### Option B: Pre-generate with analysis script

For advanced users who want to inspect or customize the metadata:

```bash
# Set your API keys
export OPENAI_API_KEY="your_key"
export API_BASE="http://your_api/v1"
export LANGUAGE_MODEL="openai/gpt-4.1"
export VISION_MODEL="openai/gpt-4.1"

# Run analysis script (you'll need to create this)
python -c "
import asyncio
from pptagent.presentation import Presentation
from pptagent.induct import SlideInducter
from pptagent.model_utils import ModelManager
from pptagent.utils import Config, package_join
import json
from os.path import join

async def analyze_template(template_name):
    config = Config(package_join('templates', template_name))
    models = ModelManager()

    # Load presentation
    presentation = Presentation.from_file(
        join(config.RUN_DIR, 'source.pptx'),
        config
    )

    # Run slide induction
    inducter = SlideInducter(
        presentation,
        join(config.RUN_DIR, 'slide_images'),
        join(config.RUN_DIR, 'template_images'),
        config,
        models.image_model,
        models.language_model,
        models.vision_model,
    )

    layout_induction = await inducter.layout_induct()
    slide_induction = await inducter.content_induct(layout_induction)

    # Save metadata
    with open(join(config.RUN_DIR, 'slide_induction.json'), 'w') as f:
        json.dump(slide_induction, f, ensure_ascii=False, indent=4)

    print(f'Generated slide_induction.json for {template_name}')

asyncio.run(analyze_template('my-corporate-template'))
"
```

**Note**: The auto-generation approach is recommended unless you need to customize the metadata manually.

### 4. Add Description

Create a concise description that appears in the template selector:

```bash
cat > pptagent/templates/$TEMPLATE_NAME/description.txt << 'EOF'
A modern corporate template with clean layouts and professional typography, suitable for business reports and executive presentations.
EOF
```

**Tips for good descriptions**:
- Keep it to 1-2 sentences
- Mention the template's visual style
- Indicate intended use cases
- Mention any special features (e.g., "includes data visualization slides")

**Examples**:
```
A LaTeX Beamer-style template suitable for academic presentations, technical talks, and conferences.
```
```
A minimalist template with bold typography and vibrant colors, ideal for startup pitches and creative projects.
```
```
A presentation template tailored for Harbin Institute of Technology style.
```

### 5. Generate Preview Image

Run the automated preview generation script:

```bash
# Generate previews for all templates (including new ones)
./scripts/generate_template_previews.sh

# Or generate for a specific template
soffice --headless --convert-to png \
  --outdir pptagent/templates/$TEMPLATE_NAME \
  pptagent/templates/$TEMPLATE_NAME/source.pptx

# Rename the output to preview.png
mv pptagent/templates/$TEMPLATE_NAME/source.png \
   pptagent/templates/$TEMPLATE_NAME/preview.png
```

**Requirements**:
- LibreOffice must be installed (`soffice` command)
- The script generates a PNG from the first slide
- Recommended size: 800x600px or template's native resolution

---

## Template Design Best Practices

### Content Slide Design

1. **Text-heavy slides**: Use bullet points, numbered lists, or multi-column layouts
2. **Image-heavy slides**: Include large placeholder images with captions
3. **Mixed slides**: Combine text and images in balanced layouts

### Color and Typography

- Use consistent color schemes across all slides
- Limit to 2-3 font families maximum
- Ensure sufficient contrast for readability
- Test on projectors/screens (avoid pure white backgrounds)

### Placeholders and Elements

PPTAgent recognizes these element types:
- **TextBox**: Regular text frames
- **Picture**: Images and photos
- **Table**: Data tables
- **Chart**: Placeholder charts
- **GroupShape**: Grouped elements (avoid nesting)

### Background Images

Images covering >95% of the slide area are treated as backgrounds. Use the `hide_small_pic_ratio` parameter to control how small decorative images are handled.

### Multi-language Support

If your template targets specific languages:
- Design layouts considering text expansion (Latin→CJK ~2x longer, CJK→Latin ~0.5x shorter)
- Use appropriate font families (e.g., SimSun for Chinese, Arial for English)
- Test with sample content in the target language

---

## Testing Your Template

### 1. Web UI Testing

Start the backend and test through the UI:

```bash
# Set environment variables
export OPENAI_API_KEY="your_key"
export API_BASE="http://your_api/v1"
export LANGUAGE_MODEL="openai/gpt-4.1"
export VISION_MODEL="openai/gpt-4.1"

# Start backend
python pptagent_ui/backend.py

# Start frontend (in another terminal)
cd pptagent_ui
npm run serve
```

Navigate to `http://localhost:8080` and select your template from the dropdown.

### 2. MCP Server Testing

```bash
export PPTAGENT_MODEL=openai/gpt-4.1
export PPTAGENT_API_BASE=http://localhost:8000/v1
export PPTAGENT_API_KEY=your_key

uv run pptagent-mcp
```

In Claude/Cursor, use the `list_templates` and `set_template` tools.

### 3. Programmatic Testing

```python
import asyncio
from pptagent.pptgen import PPTAgent
from pptagent.document import Document
from pptagent.model_utils import ModelManager
from pptagent.utils import package_join

async def test_template():
    models = ModelManager()
    agent = PPTAgent(models.language_model, models.vision_model)

    # Set your template
    agent.set_reference_from_file(package_join('templates', 'my-corporate-template'))

    # Load test document
    doc = await Document.from_markdown(
        "# Test\n\nThis is a test presentation.",
        models.language_model,
        models.vision_model,
    )

    # Generate presentation
    pres, _ = await agent.generate_pres(doc, num_slides=5)
    pres.save('test_output.pptx')
    print("Test successful!")

asyncio.run(test_template())
```

---

## Troubleshooting

### Template not appearing in UI

**Cause**: Missing required files or incorrect directory structure

**Solution**:
```bash
# Verify template structure
ls -la pptagent/templates/your-template/

# Required files: source.pptx, description.txt
# Check file permissions
chmod 644 pptagent/templates/your-template/*
```

### "Slide parsing failed" errors

**Cause**: Template contains unsupported elements

**Solution**:
1. Open `source.pptx` in PowerPoint
2. Check for unsupported elements (see [Elements to Avoid](#-elements-to-avoid))
3. Simplify complex shapes or replace SmartArt with basic shapes
4. Check backend logs for specific error messages

### Generated slides don't match template style

**Cause**: Metadata files are stale or corrupted

**Solution**:
```bash
# Delete auto-generated files
rm pptagent/templates/your-template/slide_induction.json
rm pptagent/templates/your-template/image_stats.json

# Regenerate on next use
python -c "
from pptagent.mcp_server import PPTAgentServer
server = PPTAgentServer()
server.set_template('your-template')
"
```

### Preview image not generating

**Cause**: LibreOffice not installed or PPTX file corrupted

**Solution**:
```bash
# Check LibreOffice installation
which soffice

# Install if missing (Ubuntu/Debian)
sudo apt-get install libreoffice

# Test PPTX file
soffice --headless --convert-to pdf pptagent/templates/your-template/source.pptx

# If conversion fails, re-export PPTX from PowerPoint
```

### Text overflow or formatting issues

**Cause**: Text frame settings not configured correctly

**Solution**:
1. Open template in PowerPoint
2. Select all text boxes (Ctrl+A)
3. Right-click → Format Shape → Text Options → Text Box
4. Set **"Shrink text on overflow"**
5. Save and regenerate metadata

---

## Examples

Browse the [existing templates](pptagent/templates/) for reference:

- **default**: General-purpose template with deep green theme
- **beamer**: LaTeX Beamer-style for academic presentations
- **cip**: Chinese Academy of Sciences institutional style
- **hit**: Harbin Institute of Technology style
- **thu**: Tsinghua University style
- **ucas**: UCAS institutional style

Study these templates to understand layout variety, content organization, and design patterns.

---

## Contributing Templates

To contribute your template to PPTAgent:

1. Ensure your template follows all best practices
2. Test thoroughly with different document types
3. Add proper `description.txt` and generate preview
4. Submit a pull request with your template directory

**Licensing**: All contributed templates should be freely licensed (MIT, CC BY, or public domain).

---

## Additional Resources

- [BESTPRACTICE.md](BESTPRACTICE.md) - Detailed design guidelines and parameter settings
- [DOC.md](DOC.md) - Full project documentation
- [python-pptx documentation](https://python-pptx.readthedocs.io/) - Understanding element types and limitations

---

**Need help?** Open an issue on GitHub or consult the documentation. Happy template creation! 🎉
