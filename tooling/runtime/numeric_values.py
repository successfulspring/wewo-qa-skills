"""Shared exact finite-decimal parsing for design and observation contracts."""
from decimal import Decimal, InvalidOperation, localcontext


def finite_decimal(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise ValueError("expected finite decimal value")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("expected finite decimal value") from exc
    if not result.is_finite():
        raise ValueError("expected finite decimal value")
    return result


def decimal_sum(left, right):
    left, right = finite_decimal(left), finite_decimal(right)
    with localcontext() as context:
        context.prec = max(28, max(left.adjusted(), right.adjusted()) - min(left.as_tuple().exponent, right.as_tuple().exponent) + 3)
        return left + right
