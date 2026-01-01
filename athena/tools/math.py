"""Mathematical expression evaluation tool."""

import ast
import math
import operator
from typing import Any, Dict, Callable
from athena.models.tool import Tool, ToolParameter, ToolParameterType, ToolResult


class MathTool(Tool):
    """Safe mathematical expression evaluator.

    Provides accurate mathematical calculations without relying on the LLM,
    which can make arithmetic errors. Safer and more efficient than model-based math.
    """

    @property
    def name(self) -> str:
        return "Math"

    @property
    def description(self) -> str:
        return """Evaluate mathematical expressions safely and accurately.

Use this instead of trying to calculate in your head - it's always accurate!

Supports:
- Basic arithmetic: +, -, *, /, //, %, **
- Comparisons: <, >, <=, >=, ==, !=
- Functions: sin, cos, tan, asin, acos, atan, sqrt, log, log10, abs, round, ceil, floor, factorial, gcd, degrees, radians
- Constants: pi, e
- Large numbers and high precision (no token limits!)

Examples:
- "123 * 456" → 56088
- "sqrt(144)" → 12.0
- "sin(pi/4)" → 0.7071067811865476
- "2**100" → 1267650600228229401496703205376
- "factorial(20)" → 2432902008176640000
- "log10(1000)" → 3.0
- "gcd(48, 18)" → 6
- "degrees(pi/2)" → 90.0

IMPORTANT: Always use this tool for calculations instead of doing math yourself!
The model can make arithmetic errors, but this tool is always accurate."""

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="expression",
                type=ToolParameterType.STRING,
                description="Mathematical expression to evaluate (e.g., '2 + 2', 'sqrt(16)', 'sin(pi/4)')",
                required=True,
            ),
        ]

    async def execute(self, expression: str, **kwargs: Any) -> ToolResult:
        """Safely evaluate mathematical expression.

        Args:
            expression: Math expression to evaluate

        Returns:
            ToolResult with calculated value
        """
        try:
            # Define safe operations
            safe_operators = {
                ast.Add: operator.add,
                ast.Sub: operator.sub,
                ast.Mult: operator.mul,
                ast.Div: operator.truediv,
                ast.FloorDiv: operator.floordiv,
                ast.Mod: operator.mod,
                ast.Pow: operator.pow,
                ast.USub: operator.neg,
                ast.UAdd: operator.pos,
                # Comparisons
                ast.Lt: operator.lt,
                ast.LtE: operator.le,
                ast.Gt: operator.gt,
                ast.GtE: operator.ge,
                ast.Eq: operator.eq,
                ast.NotEq: operator.ne,
            }

            # Define safe functions and constants
            safe_names = {
                # Trigonometric functions
                'sin': math.sin,
                'cos': math.cos,
                'tan': math.tan,
                'asin': math.asin,
                'acos': math.acos,
                'atan': math.atan,
                'atan2': math.atan2,
                'sinh': math.sinh,
                'cosh': math.cosh,
                'tanh': math.tanh,

                # Exponential and logarithmic
                'exp': math.exp,
                'log': math.log,
                'log10': math.log10,
                'log2': math.log2,
                'sqrt': math.sqrt,

                # Power and roots
                'pow': pow,

                # Rounding
                'abs': abs,
                'round': round,
                'ceil': math.ceil,
                'floor': math.floor,
                'trunc': math.trunc,

                # Special functions
                'factorial': math.factorial,
                'gcd': math.gcd,

                # Conversion
                'degrees': math.degrees,
                'radians': math.radians,

                # Constants
                'pi': math.pi,
                'e': math.e,
                'tau': math.tau,
                'inf': math.inf,
                'nan': math.nan,

                # Min/max
                'min': min,
                'max': max,

                # Sum (for lists)
                'sum': sum,
            }

            # Parse the expression
            parsed = ast.parse(expression, mode='eval')

            # Evaluate safely
            result = self._eval_node(parsed.body, safe_operators, safe_names)

            # Format result nicely
            if isinstance(result, float):
                # Show reasonable precision
                if result == int(result):
                    output = str(int(result))
                else:
                    output = str(result)
            elif isinstance(result, bool):
                output = str(result)
            else:
                output = str(result)

            return ToolResult(
                success=True,
                output=output,
                metadata={
                    "expression": expression,
                    "result": result,
                    "type": type(result).__name__,
                },
            )

        except ZeroDivisionError:
            return ToolResult(
                success=False,
                output="",
                error="Division by zero",
            )
        except ValueError as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Invalid value: {str(e)}",
            )
        except SyntaxError as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Invalid expression syntax: {str(e)}",
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Evaluation failed: {str(e)}",
            )

    def _eval_node(
        self,
        node: ast.AST,
        operators: Dict[type, Callable],
        names: Dict[str, Any],
    ) -> Any:
        """Recursively evaluate AST node safely.

        Args:
            node: AST node to evaluate
            operators: Allowed operators
            names: Allowed names (functions/constants)

        Returns:
            Evaluated result

        Raises:
            ValueError: If unsafe operation attempted
        """
        if isinstance(node, ast.Constant):
            # Python 3.8+ - numbers, strings, etc.
            return node.value

        elif isinstance(node, ast.Name):
            # Variable/constant lookup
            if node.id in names:
                return names[node.id]
            else:
                raise ValueError(f"Unsafe name: {node.id}")

        elif isinstance(node, ast.BinOp):
            # Binary operation (e.g., 2 + 3)
            if type(node.op) not in operators:
                raise ValueError(f"Unsafe operator: {type(node.op).__name__}")

            left = self._eval_node(node.left, operators, names)
            right = self._eval_node(node.right, operators, names)
            return operators[type(node.op)](left, right)

        elif isinstance(node, ast.UnaryOp):
            # Unary operation (e.g., -5)
            if type(node.op) not in operators:
                raise ValueError(f"Unsafe unary operator: {type(node.op).__name__}")

            operand = self._eval_node(node.operand, operators, names)
            return operators[type(node.op)](operand)

        elif isinstance(node, ast.Compare):
            # Comparison (e.g., 5 > 3)
            left = self._eval_node(node.left, operators, names)

            for op, comparator in zip(node.ops, node.comparators):
                if type(op) not in operators:
                    raise ValueError(f"Unsafe comparison: {type(op).__name__}")

                right = self._eval_node(comparator, operators, names)
                result = operators[type(op)](left, right)

                if not result:
                    return False
                left = right

            return True

        elif isinstance(node, ast.Call):
            # Function call (e.g., sin(0.5))
            if not isinstance(node.func, ast.Name):
                raise ValueError("Only simple function calls allowed")

            func_name = node.func.id
            if func_name not in names:
                raise ValueError(f"Unsafe function: {func_name}")

            func = names[func_name]
            args = [self._eval_node(arg, operators, names) for arg in node.args]

            # Handle keyword arguments if any
            kwargs = {}
            for keyword in node.keywords:
                kwargs[keyword.arg] = self._eval_node(keyword.value, operators, names)

            return func(*args, **kwargs)

        elif isinstance(node, ast.List):
            # List literal (e.g., [1, 2, 3])
            return [self._eval_node(item, operators, names) for item in node.elts]

        elif isinstance(node, ast.Tuple):
            # Tuple literal (e.g., (1, 2, 3))
            return tuple(self._eval_node(item, operators, names) for item in node.elts)

        else:
            raise ValueError(f"Unsafe node type: {type(node).__name__}")
