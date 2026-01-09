# Fritzing Diagram Generator - Development Roadmap

## Vision
An AI-powered tool that reads natural language wiring instructions, matches components from the Fritzing library, generates .fzz files, and produces 1090x1080 breadboard layout images.

---

## Phase 1: Fritzing Format Understanding
**Goal: Parse and generate basic .fzz files**

- [ ] Research .fzz file structure (XML + ZIP format)
- [ ] Extract and analyze sample .fzz files
- [ ] Map out XML schema for:
  - Component placement (breadboard view)
  - Wire routing
  - Component references/IDs
  - View metadata
- [ ] Create minimal .fzz file generator (proof of concept)
- [ ] Validate generated .fzz files open in Fritzing app

**Deliverable:** Python script that creates a basic valid .fzz file with 2-3 components

---

## Phase 2: Fritzing Parts Library Integration
**Goal: Load and utilize existing Fritzing components**

- [ ] Locate Fritzing parts library on system
  - Default paths: `/Applications/Fritzing.app/Contents/Resources/parts/` (macOS)
  - User library: `~/Documents/Fritzing/parts/`
- [ ] Parse .fzp (Fritzing Part) XML files
- [ ] Extract component metadata:
  - Component name/label
  - Pin/connector definitions
  - SVG references for breadboard view
  - Component categories (Arduino, LED, resistor, etc.)
- [ ] Build searchable component index:
  - By name (e.g., "Arduino Uno")
  - By type (e.g., "LED", "resistor")
  - By category
- [ ] Create component matcher function:
  - Input: Natural language description
  - Output: Best matching Fritzing part

**Deliverable:** Component library loader + fuzzy search/matching system

---

## Phase 3: Natural Language Instruction Parser
**Goal: Convert wiring instructions to structured data**

- [ ] Design instruction parsing strategy:
  - LLM-based parsing (use Claude to extract structure)
  - Pattern matching for common phrases
  - Entity extraction (component names, pins, values)
- [ ] Define intermediate representation:
  ```python
  {
    "components": [
      {"id": "arduino1", "type": "Arduino Uno", "position": (x, y)},
      {"id": "led1", "type": "LED", "color": "red", "position": (x, y)},
      {"id": "r1", "type": "Resistor", "value": "220Ω", "position": (x, y)}
    ],
    "connections": [
      {"from": ("arduino1", "pin 13"), "to": ("r1", "leg1")},
      {"from": ("r1", "leg2"), "to": ("led1", "anode")},
      {"from": ("led1", "cathode"), "to": ("arduino1", "GND")}
    ]
  }
  ```
- [ ] Parse component specifications:
  - Component type (Arduino, LED, resistor)
  - Properties (resistance value, LED color, IC type)
  - Quantity
- [ ] Parse connection specifications:
  - Source component + pin/terminal
  - Destination component + pin/terminal
  - Wire properties (color, optional)
- [ ] Handle common instruction formats:
  - "Connect Arduino pin 13 to resistor"
  - "LED anode to resistor, cathode to ground"
  - "220 ohm resistor between pin 13 and LED"

**Deliverable:** Instruction parser that outputs structured component + connection data

---

## Phase 4: Breadboard Layout Engine
**Goal: Automatically position components on virtual breadboard**

- [ ] Define breadboard grid system:
  - Standard breadboard dimensions
  - Row/column mapping (a-j, 1-63, etc.)
  - Power rails vs signal rows
- [ ] Implement component placement algorithm:
  - Auto-arrange components to minimize wire crossings
  - Respect component footprints
  - Leave reasonable spacing
  - Option for manual position hints
- [ ] Wire routing algorithm:
  - Find paths between connection points
  - Follow breadboard topology (connected rows)
  - Avoid wire overlaps where possible
  - Calculate wire lengths
- [ ] Layout optimization:
  - Compact layouts
  - Clean wire routing
  - Power/ground rail usage

**Deliverable:** Layout engine that places components and routes wires on breadboard

---

## Phase 5: .fzz File Generation
**Goal: Generate complete Fritzing project files**

- [ ] Generate .fzz XML structure:
  - Project metadata
  - Component instances with positions
  - Wire definitions with paths
  - View settings (zoom, pan, active view)
- [ ] Reference Fritzing parts correctly:
  - Use proper part IDs from library
  - Link to SVG resources
  - Set component properties
- [ ] Handle breadboard-specific elements:
  - Breadboard grid snapping
  - Connector placement
  - Wire bend points
- [ ] Package as .fzz (ZIP):
  - Main .fz XML file
  - Referenced SVGs (if custom parts)
  - Metadata
- [ ] Validate output:
  - XML schema validation
  - Open in Fritzing successfully
  - Verify all connections visible

**Deliverable:** Complete .fzz file generator from structured data

---

## Phase 6: Image Rendering
**Goal: Export 1090x1080 breadboard view images**

### Option A: Use Fritzing CLI/Headless
- [ ] Research Fritzing command-line export
- [ ] Automate: .fzz → PNG export
- [ ] Set image dimensions (1090x1080)
- [ ] Set view (breadboard only)

### Option B: Custom SVG Renderer
- [ ] Parse breadboard view from .fzz
- [ ] Render components using Fritzing SVGs
- [ ] Render wires/connections
- [ ] Composite into final image
- [ ] Export as PNG (1090x1080)

### Option C: Headless Fritzing via PyQt
- [ ] Load Fritzing as library (if possible)
- [ ] Programmatically open .fzz
- [ ] Export breadboard view
- [ ] Control dimensions

**Deliverable:** Reliable PNG image export at 1090x1080

---

## Phase 7: Athena Tool Integration
**Goal: Make it usable as an Athena tool**

- [ ] Create `FritzingDiagramTool` class:
  - Inherit from `Tool` base class
  - Define tool name, description, parameters
- [ ] Parameters:
  - `instructions` (str): Natural language wiring instructions
  - `output_path` (str, optional): Where to save .fzz file
  - `image_only` (bool): Only return image, skip .fzz generation
- [ ] Output format:
  - Base64-encoded PNG image
  - Path to generated .fzz file (optional)
  - Component list used
  - Connection summary
- [ ] Error handling:
  - Component not found in library
  - Ambiguous connections
  - Layout impossible (too many components)
  - Invalid instructions
- [ ] Register tool in `__init__.py`

**Deliverable:** Fully functional Athena tool

---

## Phase 8: Testing & Refinement

- [ ] Test with common circuits:
  - Arduino + LED + resistor
  - Button input circuit
  - Sensor connections (temp, ultrasonic, etc.)
  - Motor control circuits
  - Multi-LED projects
- [ ] Edge cases:
  - Complex circuits (10+ components)
  - Ambiguous instructions
  - Missing components in library
  - Conflicting wire routes
- [ ] Performance optimization:
  - Component search speed
  - Layout algorithm efficiency
  - Image generation time
- [ ] User experience:
  - Clear error messages
  - Helpful suggestions when components not found
  - Preview/validation before generation

**Deliverable:** Robust, tested tool ready for production

---

## Phase 9: Advanced Features (Future)

- [ ] Support multiple views:
  - Breadboard
  - Schematic (auto-generate from breadboard)
  - PCB layout (stretch goal)
- [ ] Component library expansion:
  - Import custom parts
  - Auto-download missing components
  - Create basic components on-the-fly
- [ ] Interactive refinement:
  - "Move Arduino to the left"
  - "Use a blue wire instead"
  - "Make layout more compact"
- [ ] Style customization:
  - Wire colors
  - Background color
  - Component labeling
- [ ] Export formats:
  - PDF
  - SVG
  - Multiple image sizes
- [ ] Circuit validation:
  - Check for shorts
  - Voltage/current warnings
  - Component compatibility

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────┐
│           FritzingDiagramTool (Athena)              │
│  - Natural language instructions input              │
│  - Orchestrates entire pipeline                     │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│        Instruction Parser (LLM-based)               │
│  - Extract components and connections               │
│  - Output: Structured IR                            │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│       Component Matcher & Library                   │
│  - Fritzing parts index                             │
│  - Fuzzy matching: description → .fzp file          │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│         Breadboard Layout Engine                    │
│  - Auto-arrange components                          │
│  - Route wires                                      │
│  - Optimize layout                                  │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│            .fzz Generator                           │
│  - Create XML structure                             │
│  - Package as ZIP                                   │
│  - Validate output                                  │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│          Image Renderer                             │
│  - Render breadboard view                           │
│  - Export as 1090x1080 PNG                          │
│  - Return base64                                    │
└─────────────────────────────────────────────────────┘
```

---

## Dependencies

- **Python packages:**
  - `xml.etree.ElementTree` - XML parsing/generation
  - `zipfile` - .fzz packaging
  - `Pillow` or `cairosvg` - SVG → PNG rendering
  - `fuzzywuzzy` or `rapidfuzz` - Component name matching
  - Optional: `networkx` - Wire routing graphs

- **External:**
  - Fritzing application (for parts library)
  - Optional: Fritzing CLI for rendering

---

## Open Questions

1. **Fritzing availability:** Do we require Fritzing installed, or bundle parts library?
2. **Layout algorithm:** Simple grid-based or graph-based optimization?
3. **Component ambiguity:** How to handle "LED" when library has 50 LED variants?
4. **Wire routing:** Manual hints or fully automatic?
5. **Rendering approach:** Which option (A/B/C) for image generation?
6. **License:** Fritzing parts library usage rights?

---

## Success Criteria

A user can say:
> "Create a breadboard diagram: Arduino Uno pin 13 connected to a 220 ohm resistor, then to a red LED, with LED cathode to ground"

And receive:
- A valid .fzz file they can open in Fritzing
- A clean 1090x1080 PNG image showing the layout
- All components correctly identified and placed
- All wires routed properly
