import base64
from io import BytesIO
from typing import Dict, Any

import schemdraw
import schemdraw.elements as elm

from athena.models.tool import Tool, ToolParameter, ToolParameterType, ToolResult


class GenerateCircuitDiagramTool(Tool):
    @property
    def name(self) -> str:
        return "generate_circuit_diagram"

    @property
    def description(self) -> str:
        return (
            "Generates a clean, professional schematic diagram (PNG image) "
            "based on a natural language description of an electronic circuit. "
            "Supports common circuits like LED with resistor, RC filters, "
            "voltage dividers, op-amp configurations, Arduino connections, etc. "
            "Returns base64-encoded PNG in the output."
        )

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="description",
                type=ToolParameterType.STRING,
                description=(
                    "Natural language description of the desired circuit. "
                    "Be as specific as possible (e.g., 'Arduino Uno pin 13 connected to a red LED "
                    "through a 220 ohm resistor, with cathode to GND')."
                ),
                required=True,
            )
        ]

    def _generate_diagram(self, description: str) -> str:
        """Generate Schemdraw diagram based on description and return base64 PNG."""
        desc = description.lower()

        with schemdraw.Drawing() as d:
            # Simple blinking LED (common Arduino circuit)
            if "led" in desc and ("220" in desc or "resistor" in desc) and ("arduino" in desc or "pin 13" in desc):
                arduino = d.add(elm.Ic(pins=18, label='Arduino Uno\nPin 13'))
                d += elm.Line().left().at(arduino.pin(7))  # Approximate pin 13 position
                d += elm.Resistor().right().label('220Ω')
                d += elm.LED().right().label('LED')
                d += elm.Ground()

            # Basic LED circuit (no Arduino)
            elif "led" in desc and "resistor" in desc:
                d += elm.SourceV().label('5V')
                d += elm.Resistor().right().label('220Ω' if '220' in desc else 'R')
                d += elm.LED().right().label('LED')
                d += elm.Ground()

            # RC low-pass filter
            elif ("rc" in desc or ("resistor" in desc and "capacitor" in desc and "filter" in desc)):
                d += elm.SourceSin().label('Vin')
                d += elm.Resistor().right().label('10kΩ')
                d += elm.Capacitor().down().label('1μF')
                d += elm.Ground()
                d += elm.Line().left().to(d.here)  # Close loop
                d += elm.Dot().at(elm.Resistor.end)
                d += elm.Label().at(elm.Dot()).label('Vout')

            # Voltage divider
            elif "voltage divider" in desc or ("r1" in desc and "r2" in desc):
                d += elm.SourceV().label('Vin')
                d += elm.Resistor().down().label('R1\n10kΩ')
                d += elm.Resistor().down().label('R2\n10kΩ')
                d += elm.Ground()
                mid = d.here
                d.move(-2, 1)
                d += elm.Line().right().to(mid)
                d += elm.Dot()
                d += elm.Label().label('Vout')

            # Op-amp non-inverting amplifier
            elif "op-amp" in desc and ("non-inverting" in desc or "amplifier" in desc):
                op = d.add(elm.Opamp())
                d += elm.Resistor().to(op.in2).label('Rf\n10kΩ').dot()
                d += elm.Line().to(op.out)
                d += elm.Resistor().to(op.in2).down().label('Rin\n1kΩ').to(elm.Ground())
                d += elm.SourceSin().up().at(op.in1).label('Vin')
                d += elm.Line().to(op.in1)

            # Default fallback: simple series resistor-capacitor
            else:
                d += elm.SourceV().label('V')
                d += elm.Resistor().right().label('R')
                d += elm.Capacitor().right().label('C')
                d += elm.Ground()

            # Save to buffer
            buf = BytesIO()
            d.save(buf, format='png', dpi=150)
            return base64.b64encode(buf.getvalue()).decode('utf-8')

    async def execute(self, description: str, **kwargs) -> ToolResult:
        try:
            img_base64 = self._generate_diagram(description)

            return ToolResult(
                success=True,
                output=(
                    "Circuit diagram generated successfully!\n\n"
                    f"Base64-encoded PNG (copy and decode to view/save):\n\n{img_base64}"
                ),
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to generate diagram: {str(e)}"
            )enerate_circuit_diagram.py
