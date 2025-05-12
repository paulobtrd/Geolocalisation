# // UWB projet Localisation
# // Olivier CONET/Paul Bertrand
# // source https://github.com/Makerfabs/Makerfabs-ESP32-UWB/tree/main
# // Version 30 avril 2025
# // Resultat : Testé OK avec tag sur batterie et anchor AA11 et AA22
# le PC et le tag doivent être connectés au même WiFi



import time
import turtle
import cmath
import socket
import json

hostname = socket.gethostname()
UDP_IP = socket.gethostbyname(hostname)
print("***Local ip:" + str(UDP_IP) + "***")
UDP_PORT = 5050
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((UDP_IP, UDP_PORT))
sock.listen(1)  # 接收的连接数
data, addr = sock.accept()

distance_a1_a2 = 20
meter2pixel = 25
range_offset = 0.9


def screen_init(width=1200, height=1200, t=turtle):
    t.setup(width, height)
    t.tracer(False)
    t.hideturtle()
    t.speed(0)


def turtle_init(t=turtle):
    t.hideturtle()
    t.speed(0)


def draw_line(x0, y0, x1, y1, color="black", t=turtle):
    t.pencolor(color)

    t.up()
    t.goto(x0, y0)
    t.down()
    t.goto(x1, y1)
    t.up()


def draw_fastU(x, y, length, color="black", t=turtle):
    draw_line(x, y, x, y + length, color, t)


def draw_fastV(x, y, length, color="black", t=turtle):
    draw_line(x, y, x + length, y, color, t)


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


def draw_rect(x, y, w, h, color="black", t=turtle):
    t.pencolor(color)

    t.up()
    t.goto(x, y)
    t.down()
    t.goto(x + w, y)
    t.goto(x + w, y + h)
    t.goto(x, y + h)
    t.goto(x, y)
    t.up()


def fill_rect(x, y, w, h, color=("black", "black"), t=turtle):
    t.begin_fill()
    draw_rect(x, y, w, h, color, t)
    t.end_fill()
    pass


def clean(t=turtle):
    t.clear()


def draw_ui(t):
    # Titre
    #write_txt(-300, 250, "UWB Indoor Positioning", "black", t, f=('Arial', 32, 'normal'))
    
    # Définir les points de la salle en mètres (en utilisant le plan comme référence)
    # Les mesures sont approximatives basées sur le plan, adaptées pour votre système de coordonnées
    # Point (0,0) correspond à l'ancre AA11 dans votre système
    room_points = [
        (0, 0),         # Point de départ, coin inférieur gauche
        (20, 0),      # Coin inférieur droit
        (20, 13.5),   # Coin supérieur droit
        (0, 13.5),      # Coin supérieur gauche proche des portes
        (-3, 10.5),     # Point incliné haut gauche
        (-3, 5),        # Point incliné bas gauche
        (0, 0)          # Retour au point de départ
    ]
    
    # Dessiner la salle
    draw_room_polygon(t, room_points)
    
    # Ajouter des repères pour les ancres
    write_txt(-250, 150, "AA11(0,0)", "darkgreen", t, f=('Arial', 16, 'normal'))
    write_txt(-250 + meter2pixel * distance_a1_a2, 150, 
              f"AA22({distance_a1_a2},0)", "darkgreen", t, f=('Arial', 16, 'normal'))

# Fonction pour convertir des mètres en pixels
# Fonction pour convertir des mètres en pixels
def meters_to_pixels(x_m, y_m, scale=meter2pixel):
    # Définir les dimensions exactes basées sur vos points de salle
    x_min = -3  # Point le plus à gauche
    x_max = 14.5  # Point le plus à droite
    y_min = 0  # Point le plus bas
    y_max = 13.5  # Point le plus haut
    
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


def draw_uwb_anchor(x, y, txt, range, t):
    # Utiliser les coordonnées converties
    pos_x, pos_y = meters_to_pixels(0, 0) if txt == "AA11(0,0)" else meters_to_pixels(distance_a1_a2, 0)
    
    r = 20
    fill_cycle(pos_x, pos_y, r, "green", t)
    write_txt(pos_x + r, pos_y, txt + ": " + str(range) + "M",
              "black",  t, f=('Arial', 16, 'normal'))


def draw_uwb_tag(x, y, txt, t):
    pos_x = -250 + int(x * meter2pixel)
    pos_y = 150 - int(y * meter2pixel)
    r = 20
    fill_cycle(pos_x, pos_y, r, "blue", t)
    write_txt(pos_x, pos_y, txt + ": (" + str(x) + "," + str(y) + ")",
              "black",  t, f=('Arial', 16, 'normal'))


def read_data():

    line = data.recv(1024).decode('UTF-8')

    uwb_list = []

    try:
        uwb_data = json.loads(line)
        print(uwb_data)

        uwb_list = uwb_data["links"]
        for uwb_archor in uwb_list:
            print(uwb_archor)

    except:
        print(line)
    print("")

    return uwb_list


def tag_pos(a, b, c):
    # p = (a + b + c) / 2.0
    # s = cmath.sqrt(p * (p - a) * (p - b) * (p - c))
    # y = 2.0 * s / c
    # x = cmath.sqrt(b * b - y * y)
    cos_a = (b * b + c*c - a * a) / (2 * b * c)
    x = b * cos_a
    y = b * cmath.sqrt(1 - cos_a * cos_a)

    return round(x.real, 1), round(y.real, 1)


def uwb_range_offset(uwb_range):

    temp = uwb_range
    return temp


def main():

    t_ui = turtle.Turtle()
    t_a1 = turtle.Turtle()
    t_a2 = turtle.Turtle()
    t_a3 = turtle.Turtle()
    turtle_init(t_ui)
    turtle_init(t_a1)
    turtle_init(t_a2)
    turtle_init(t_a3)

    a1_range = 0.0
    a2_range = 0.0

    draw_ui(t_ui)

    while True:
        node_count = 0
        list = read_data()

        for one in list:
            if one["A"] == "AA11":
                clean(t_a1)
                a1_range = uwb_range_offset(float(one["R"]))
                draw_uwb_anchor(-250, 150, "AA11(0,0)", a1_range, t_a1)
                node_count += 1

            if one["A"] == "AA22":
                clean(t_a2)
                a2_range = uwb_range_offset(float(one["R"]))
                draw_uwb_anchor(-250 + meter2pixel * distance_a1_a2,
                                150, "AA22(" + str(distance_a1_a2)+")", a2_range, t_a2)
                node_count += 1

        if node_count == 2:
            x, y = tag_pos(a2_range, a1_range, distance_a1_a2)
            print(x, y)
            clean(t_a3)
            draw_uwb_tag(x, y, "TAG", t_a3)

        time.sleep(0.1)

    turtle.mainloop()


if __name__ == '__main__':
    main()