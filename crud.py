

# TODO: Move db handling to a separate module or class
def create_dictionary():
    global dictionary
    dictionary = {}
    with open("database.txt", "r", encoding="utf-8") as db:
        for line in db:
            k, v = line.strip().split(":", 1)
            dictionary[k] = v


# Dictionary should be initialized beforehand

def create_entry(key, value, db):
    db.write(f"{key}:{value}\n")
    dictionary[key] = value

def read_entry(key):
    return dictionary.get(key)
    
#Key added by the one who created the entry or generated automatically??? aka Hash
#Generate dictionary from the database or try to work around the file pointer approach

DB = "db.txt"
Index = {}
indice_cargado = False

def load_db():
    global indice_cargado
    Index.clear()
    posicion = 0

    with open(DB, "rb") as f:
        for datos in f:
            linea = datos.decode("utf-8")
            clave, valor = linea.strip().split(" ", 1)
            Index[clave] = posicion
            posicion += len(datos)

    indice_cargado = True

def set_two(key, value):
    if not indice_cargado:
        load_db()
    with open(DB, "a", encoding="utf-8") as f:
        posicion = f.tell()
        f.write(f"{key} {value}\n")
    Index[key] = posicion

def get_two(key):
    if not indice_cargado:
        load_db()
    if key not in Index:
        return None
    with open(DB, "r", encoding="utf-8") as f:
        f.seek(Index[key])
        k, v = f.readline().strip().split(" ", 1)
    return {"clave": k, "valor": v}

