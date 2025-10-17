#!/bin/bash

# Template Preview Generation Script
# Generates preview.png for each PPTAgent template by converting the first slide

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEMPLATES_DIR="$PROJECT_ROOT/pptagent/templates"

echo "====================================="
echo "Template Preview Generator"
echo "====================================="
echo ""

# Check if templates directory exists
if [ ! -d "$TEMPLATES_DIR" ]; then
    echo -e "${RED}Error: Templates directory not found at $TEMPLATES_DIR${NC}"
    exit 1
fi

# Check if LibreOffice is installed
if ! command -v soffice &> /dev/null; then
    echo -e "${RED}Error: LibreOffice (soffice) not found. Please install LibreOffice.${NC}"
    echo "Install with: sudo apt-get install libreoffice"
    exit 1
fi

# Count templates
TOTAL_TEMPLATES=$(find "$TEMPLATES_DIR" -mindepth 1 -maxdepth 1 -type d | wc -l)
CURRENT=0
SUCCESS=0
SKIPPED=0
FAILED=0

echo "Found $TOTAL_TEMPLATES template directories"
echo ""

# Process each template directory
for TEMPLATE_DIR in "$TEMPLATES_DIR"/*; do
    if [ ! -d "$TEMPLATE_DIR" ]; then
        continue
    fi

    CURRENT=$((CURRENT + 1))
    TEMPLATE_NAME=$(basename "$TEMPLATE_DIR")
    SOURCE_PPTX="$TEMPLATE_DIR/source.pptx"
    PREVIEW_PNG="$TEMPLATE_DIR/preview.png"

    echo -e "${YELLOW}[$CURRENT/$TOTAL_TEMPLATES]${NC} Processing template: $TEMPLATE_NAME"

    # Check if source.pptx exists
    if [ ! -f "$SOURCE_PPTX" ]; then
        echo -e "  ${YELLOW}⊗ Skipped: source.pptx not found${NC}"
        SKIPPED=$((SKIPPED + 1))
        echo ""
        continue
    fi

    # Check if preview already exists
    if [ -f "$PREVIEW_PNG" ]; then
        echo -e "  ${GREEN}✓ Preview already exists, skipping${NC}"
        SKIPPED=$((SKIPPED + 1))
        echo ""
        continue
    fi

    # Create temporary directory for conversion
    TEMP_DIR=$(mktemp -d)
    trap "rm -rf $TEMP_DIR" EXIT

    # Convert PPTX to images using LibreOffice
    echo "  Converting slides..."
    if soffice --headless --convert-to png --outdir "$TEMP_DIR" "$SOURCE_PPTX" &> /dev/null; then
        # Find the first slide image
        # LibreOffice may output as source.png or source_1.png depending on version
        FIRST_SLIDE=$(find "$TEMP_DIR" -name "*.png" | sort | head -n 1)

        if [ -n "$FIRST_SLIDE" ]; then
            # Copy first slide as preview
            cp "$FIRST_SLIDE" "$PREVIEW_PNG"

            # Optimize PNG size (if optipng is available)
            if command -v optipng &> /dev/null; then
                optipng -quiet -o2 "$PREVIEW_PNG" 2>/dev/null || true
            fi

            echo -e "  ${GREEN}✓ Preview generated successfully${NC}"
            SUCCESS=$((SUCCESS + 1))
        else
            echo -e "  ${RED}✗ Failed: No PNG output from LibreOffice${NC}"
            FAILED=$((FAILED + 1))
        fi
    else
        echo -e "  ${RED}✗ Failed: LibreOffice conversion failed${NC}"
        FAILED=$((FAILED + 1))
    fi

    # Clean up temp directory
    rm -rf "$TEMP_DIR"
    echo ""
done

# Summary
echo "====================================="
echo "Summary"
echo "====================================="
echo "Total templates: $TOTAL_TEMPLATES"
echo -e "${GREEN}Successful: $SUCCESS${NC}"
echo -e "${YELLOW}Skipped: $SKIPPED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $SUCCESS -gt 0 ]; then
    echo -e "${GREEN}Preview generation completed!${NC}"
    exit 0
elif [ $SKIPPED -eq $TOTAL_TEMPLATES ]; then
    echo -e "${YELLOW}All previews already exist.${NC}"
    exit 0
else
    echo -e "${RED}Preview generation completed with errors.${NC}"
    exit 1
fi
