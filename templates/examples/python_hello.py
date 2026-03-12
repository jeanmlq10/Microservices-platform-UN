def process(data):
    name = data.get("name", "Mundo")
    return {"message": f"Hola {name}!", "language": "Python"}
