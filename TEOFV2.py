# // UWB projet Localisation - Version corrigée
# // Olivier CONET
# // Modifié pour ajouter l'interface web

import time
import turtle
import cmath
import socket
import json
import threading
import sys

# Tout d'abord, vérifiez que les modules nécessaires sont installés
try:
    import server
except ImportError:
    print("ERREUR: Le module server.py n'est pas trouvé dans le répertoire courant")
    print("Assurez-vous que server.py est dans le même dossier que ce script")
    sys.exit(1)

# Vérifier si les modules requis sont installés
try:
    import flask
    import qrcode
    from PIL import Image
except ImportError as e:
    print(f"ERREUR: Module manquant: {e}")
    print("Installez les dépendances requises avec: pip install flask qrcode[pil]")
    sys.exit(1)

# Configuration
hostname = socket.gethostname()
try:
    UDP_IP = socket.gethostbyname(hostname)
    print("***Local ip:" + str(UDP_IP) + "***")
except:
    print("ERREUR: Impossible d'obtenir l'adresse IP locale")
    UDP_IP = "127.0.0.1"

UDP_PORT = 5050

# Ouvrir le socket
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((UDP_IP, UDP_PORT))
    sock.listen(1)
    print(f"En attente de connexion sur {UDP_IP}:{UDP_PORT}...")
    data, addr = sock.accept()
    print(f"Connexion établie avec {addr}")
except Exception as e:
    print(f"ERREUR lors de l'initialisation du socket: {e}")
    sys.exit(1)

# Constantes
distance_a1_a2 = 14.5
meter2pixel = 25
range_offset = 0.9

# Démarrer le serveur web
try:
    server_url = server.start_server()
    print(f"Scannez le QR code pour accéder à l'interface web: {server_url}")
except Exception as e:
    print(f"ERREUR lors du démarrage du serveur web: {e}")
    server_url = None

# Initialisation de Turtle
screen = turtle.Screen()
screen_init_done = False

def screen_init(width=1200, height=1200, t=turtle):
    global screen_init_done
    try:
        t.setup(width, height)
        t.tracer(False)
        screen_init_done = True
        print("Écran Turtle initialisé avec succès")
    except Exception as e:
        print(f"ERREUR d'initialisation de l'écran Turtle: {e}")

def turtle_init(t=turtle):
    try:
        t.hideturtle()
        t.speed(0)
    except Exception as e:
        print(f"ERREUR d'initialisation de turtle: {e}")

# Les autres fonctions restent les mêmes que dans votre code...
def draw_line(x0, y0, x1, y1, color="black", t=turtle):
    t.pencolor(color)
    t.up()
    t.goto(x0, y0)
    t.down()
    t.goto(x1, y1)
    t.up()

def draw_cycle(x, y, r, color="black", t=turtle):
    t.pencolor(color)
    t.up()
    t.goto(x, y - r)
    t.setheading(0)
    t.down()
    t.circle(r)
    t.up()

def fill_cycle(x, y, r, color="black", t=turtle):
    t.up()
    t.goto(x, y)
    t.down()
    t.dot(r, color)
    t.up()

def write_txt(x, y, txt, color="black", t=turtle, f=('Arial', 12, 'normal')):
    t.pencolor(color)
    t.up()
    t.goto(x, y)
    t.down()
    t.write(txt, move=False, align='left', font=f)
    t.up()

def clean(t=turtle):
    t.clear()

# Fonction pour dessiner l'interface utilisateur
def draw_ui(t):
    # Définition des points de la salle selon le plan
    room_points = [
        (0, 0),           # Coin inférieur gauche (C7)
        (17.26, 0),       # Coin inférieur droit
        (17.26, 10.0),    # Coin supérieur droit
        (7.0, 10.0),      # Point supérieur milieu-droit
        (2.5, 10.0),      # Point supérieur milieu-gauche
        (0, 5.05),        # Point milieu gauche (C6)
        (0, 0)            # Retour au point de départ
    ]
    
    # Dessiner la salle
    draw_room_polygon(t, room_points)
    
    # Ajouter des repères pour les ancres
    write_txt(-250, 150, "AA11(0,0)", "darkgreen", t, f=('Arial', 16, 'normal'))
    write_txt(-250 + meter2pixel * distance_a1_a2, 150, 
              f"AA22({distance_a1_a2},0)", "darkgreen", t, f=('Arial', 16, 'normal'))
    
    # Ajouter un texte pour l'URL du serveur web
    if server_url:
        write_txt(-250, -300, f"Interface web: {server_url}", "blue", t, f=('Arial', 14, 'normal'))
        write_txt(-250, -330, "Scannez le QR code pour accéder à l'interface", "blue", t, f=('Arial', 14, 'normal'))

# Fonction pour dessiner un polygone représentant la salle
def draw_room_polygon(t, points_m, scale=meter2pixel):
    points_px = [meters_to_pixels(x, y, scale) for (x, y) in points_m]
    
    t.penup()
    t.goto(points_px[0])
    t.pendown()
    t.pencolor("black")
    t.fillcolor("lightgrey")
    t.begin_fill()
    for point in points_px[1:]:
        t.goto(point)
    t.end_fill()
    
    # Dessiner le contour en noir plus épais
    t.pensize(3)
    t.penup()
    t.goto(points_px[0])
    t.pendown()
    for point in points_px[1:] + [points_px[0]]:
        t.goto(point)
    t.pensize(1)  # Remettre la taille du stylo par défaut

def meters_to_pixels(x_m, y_m, scale=meter2pixel):
    # Définir les dimensions exactes basées sur vos nouveaux points de salle
    x_min = -3      # Point le plus à gauche
    x_max = 17.26   # Point le plus à droite (largeur)
    y_min = 0       # Point le plus bas
    y_max = 15      # Point le plus haut
    
    # Calculer la largeur et la hauteur exactes
    width_m = x_max - x_min
    height_m = y_max - y_min
    
    # Calculer le centre exact de la salle
    center_x_m = (x_min + x_max) / 2
    center_y_m = (y_min + y_max) / 2
    
    # Convertir en coordonnées centrées sur l'écran (0,0)
    x_px = (x_m - center_x_m) * scale
    y_px = -(y_m - center_y_m) * scale
    
    return (x_px, y_px)

def draw_uwb_anchor(x, y, txt, range, t):
    # Positions des ancres selon le nouveau plan
    if txt == "AA11(0,0)":
        pos_x, pos_y = meters_to_pixels(0, 0)  # Ancre au coin inférieur gauche (C7)
    else:
        pos_x, pos_y = meters_to_pixels(distance_a1_a2, 0)  # Ancre AA22
    
    r = 20
    fill_cycle(pos_x, pos_y, r, "green", t)
    write_txt(pos_x + r, pos_y, txt + ": " + str(range) + "M",
              "black", t, f=('Arial', 16, 'normal'))

def draw_uwb_tag(x, y, txt, t):
    pos_x = -250 + int(x * meter2pixel)
    pos_y = 150 - int(y * meter2pixel)
    r = 20
    fill_cycle(pos_x, pos_y, r, "blue", t)
    write_txt(pos_x, pos_y, txt + ": (" + str(x) + "," + str(y) + ")",
              "black", t, f=('Arial', 16, 'normal'))

# Historique des mesures valides
a1_history = []
a2_history = []
# Taille maximale de l'historique
MAX_HISTORY = 5

# Fonction pour filtrer les valeurs aberrantes
def filter_outliers(value, previous_values, min_acceptable=5.0, max_acceptable=20.0, max_change=5.0):
    """
    Filtre les valeurs aberrantes dans les données UWB
    """
    # Vérifier si la valeur est dans une plage raisonnable
    if value < min_acceptable or value > max_acceptable:
        # Utiliser la dernière valeur valide si disponible
        if previous_values:
            return previous_values[-1]
        else:
            # Sinon, limiter aux bornes
            return max(min(value, max_acceptable), min_acceptable)
    
    # Vérifier que le changement n'est pas trop brutal
    if previous_values and abs(value - previous_values[-1]) > max_change:
        # Utiliser simplement la dernière valeur valide
        return previous_values[-1]
    
    return value

def uwb_range_offset(uwb_range, device_type, range_offset=0.9):
    """
    Applique un offset et filtre les valeurs aberrantes
    """
    global a1_history, a2_history
    
    # Convertir en float et appliquer l'offset
    try:
        value = float(uwb_range) + range_offset
    except ValueError:
        # En cas d'erreur de conversion, utiliser la dernière valeur valide
        if device_type == 'AA11' and a1_history:
            return a1_history[-1]
        elif device_type == 'AA22' and a2_history:
            return a2_history[-1]
        else:
            return 0.0
    
    # Filtrer la valeur selon le dispositif
    if device_type == 'AA11':
        filtered_value = filter_outliers(value, a1_history)
        # Mettre à jour l'historique
        a1_history.append(filtered_value)
        if len(a1_history) > MAX_HISTORY:
            a1_history.pop(0)
    else:  # AA22
        filtered_value = filter_outliers(value, a2_history)
        # Mettre à jour l'historique
        a2_history.append(filtered_value)
        if len(a2_history) > MAX_HISTORY:
            a2_history.pop(0)
    
    return filtered_value

def read_data():
    try:
        line = data.recv(1024).decode('UTF-8')
        uwb_list = []

        try:
            uwb_data = json.loads(line)
            print(uwb_data)

            uwb_list = uwb_data["links"]
            for uwb_archor in uwb_list:
                print(uwb_archor)

        except json.JSONDecodeError:
            print(f"Erreur de décodage JSON: {line}")
        except KeyError:
            print(f"Format de données incorrect: {uwb_data}")
        except Exception as e:
            print(f"Erreur lors du traitement des données: {e}")
        
        return uwb_list
    except Exception as e:
        print(f"Erreur de réception des données: {e}")
        # En cas d'erreur, renvoyer une liste vide
        return []

def tag_pos(a, b, c):
    try:
        cos_a = (b * b + c*c - a * a) / (2 * b * c)
        # Limiter cos_a entre -1 et 1 pour éviter les erreurs
        cos_a = max(-1.0, min(1.0, cos_a))
        x = b * cos_a
        y = b * cmath.sqrt(1 - cos_a * cos_a)
        return round(x.real, 1), round(y.real, 1)
    except Exception as e:
        print(f"Erreur de calcul de position: {e}")
        return 0.0, 0.0

def main():
    # Initialiser les turtles
    t_ui = turtle.Turtle()
    t_a1 = turtle.Turtle()
    t_a2 = turtle.Turtle()
    t_a3 = turtle.Turtle()
    turtle_init(t_ui)
    turtle_init(t_a1)
    turtle_init(t_a2)
    turtle_init(t_a3)

    # Initialiser l'écran
    if not screen_init_done:
        screen_init()

    # Variables pour les distances
    a1_range = 0.0
    a2_range = 0.0

    # Dessiner l'interface utilisateur
    draw_ui(t_ui)
    
    print("Système initialisé, démarrage de la boucle principale...")
    print(f"Interface web accessible à: {server_url}")
    print("Appuyez sur Ctrl+C pour arrêter le programme")

    # Boucle principale
    try:
        while True:
            node_count = 0
            list = read_data()

            for one in list:
                if one["A"] == "AA11":
                    clean(t_a1)
                    a1_range = uwb_range_offset(float(one["R"]), "AA11")
                    draw_uwb_anchor(-250, 150, "AA11(0,0)", a1_range, t_a1)
                    node_count += 1

                if one["A"] == "AA22":
                    clean(t_a2)
                    a2_range = uwb_range_offset(float(one["R"]), "AA22")
                    draw_uwb_anchor(-250 + meter2pixel * distance_a1_a2,
                                    150, "AA22(" + str(distance_a1_a2)+")", a2_range, t_a2)
                    node_count += 1

            if node_count == 2:
                # Calculer la position
                x, y = tag_pos(a2_range, a1_range, distance_a1_a2)
                print(f"Position calculée: ({x}, {y})")
                
                # Mettre à jour l'affichage Turtle
                clean(t_a3)
                draw_uwb_tag(x, y, "TAG", t_a3)
                
                # Mettre à jour l'interface web
                if server_url:
                    try:
                        server.update_position(x, y, a1_range, a2_range)
                    except Exception as e:
                        print(f"Erreur lors de la mise à jour de l'interface web: {e}")
            
            # Mettre à jour l'affichage Turtle
            turtle.update()
            
            # Petite pause pour éviter de surcharger le CPU
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\nArrêt du programme demandé par l'utilisateur")
    except Exception as e:
        print(f"Erreur dans la boucle principale: {e}")
    finally:
        # Nettoyage des ressources
        try:
            data.close()
            sock.close()
        except:
            pass
        print("Programme terminé")

if __name__ == '__main__':
    main()