def process(data):
    a = float(data.get("a", 0))
    b = float(data.get("b", 0))
    result = a + b
    return {"a": a, "b": b, "sum": result, "language": "Python"}
