from flask import Flask, render_template, jsonify
import socket
import qrcode
import threading
import time
import os
import subprocess
import json
import urllib.request

# Créer le dossier static s'il n'existe pas
os.makedirs('static', exist_ok=True)
os.makedirs('templates', exist_ok=True)

app = Flask(__name__)

# Stockage des données de position
position_data = {
    "tag_x": 0,
    "tag_y": 0,
    "a1_range": 0,
    "a2_range": 0,
    "last_update": time.time()
}

def get_local_ip():
    """Récupère l'adresse IP locale de la machine"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Ne se connecte pas réellement
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def get_ngrok_url():
    """Obtient l'URL publique de ngrok si disponible"""
    try:
        # Vérifier si ngrok est installé
        try:
            subprocess.run(["ngrok", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            print("ngrok n'est pas installé ou n'est pas dans le PATH.")
            print("Téléchargez-le depuis https://ngrok.com/download")
            return None
        
        # Vérifier si ngrok est déjà en cours d'exécution
        try:
            response = urllib.request.urlopen("http://localhost:4040/api/tunnels")
            data = json.loads(response.read().decode())
            for tunnel in data["tunnels"]:
                if tunnel["proto"] == "https":
                    print(f"Tunnel ngrok détecté: {tunnel['public_url']}")
                    return tunnel["public_url"]
            print("Aucun tunnel HTTPS ngrok n'est en cours d'exécution.")
        except Exception as e:
            print(f"Erreur lors de la vérification des tunnels ngrok: {e}")
        
        # Lancer ngrok s'il n'est pas déjà en cours d'exécution
        print("Démarrage de ngrok...")
        # Lancer ngrok en arrière-plan
        ngrok_process = subprocess.Popen(
            ["C:/Users/paulb/Desktop/ngrok.exe", "http", "5000"], 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Attendre que le tunnel soit établi
        time.sleep(2)  # Attendre que ngrok démarre
        
        # Vérifier si le tunnel a été créé
        try:
            response = urllib.request.urlopen("http://localhost:4040/api/tunnels")
            data = json.loads(response.read().decode())
            for tunnel in data["tunnels"]:
                if tunnel["proto"] == "https":
                    print(f"Tunnel ngrok créé: {tunnel['public_url']}")
                    return tunnel["public_url"]
            print("Impossible de créer un tunnel ngrok.")
        except Exception as e:
            print(f"Erreur lors de la création du tunnel ngrok: {e}")
        
        return None
    except Exception as e:
        print(f"Erreur lors de l'utilisation de ngrok: {e}")
        return None

def generate_qr_code(url):
    """Génère un QR code pour l'URL donnée"""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        # Créer et sauvegarder l'image
        img = qr.make_image(fill_color="black", back_color="white")
        img.save("static/qrcode.png")
        return "static/qrcode.png"
    except ImportError:
        print("ERREUR: Module qrcode non installé. Lancez 'pip install qrcode[pil]'")
        return None
    except Exception as e:
        print(f"ERREUR: Impossible de générer le QR code: {e}")
        return None

@app.route('/')
def index():
    """Page principale pour afficher la position du tag"""
    return render_template('index.html')

@app.route('/api/position', methods=['GET'])
def get_position():
    """API pour récupérer les données de position actuelles"""
    return jsonify(position_data)

def update_position(x, y, a1_range, a2_range):
    """Met à jour les données de position"""
    position_data["tag_x"] = x
    position_data["tag_y"] = y
    position_data["a1_range"] = a1_range
    position_data["a2_range"] = a2_range
    position_data["last_update"] = time.time()
    # Debug: afficher la mise à jour
    print(f"Web: Position mise à jour: ({x}, {y}), A1: {a1_range}m, A2: {a2_range}m")

def start_server():
    """Démarre le serveur Flask dans un thread séparé"""
    host = get_local_ip()
    port = 5000
    local_url = f"http://{host}:{port}"
    
    # Essayer d'obtenir une URL publique via ngrok
    public_url = get_ngrok_url()
    url = public_url if public_url else local_url
    
    # Générer le QR code
    qr_path = generate_qr_code(url)
    if qr_path:
        print(f"QR code généré: {qr_path}")
    
    # Démarrer le serveur dans un thread séparé
    def run_server():
        try:
            app.run(host='0.0.0.0', port=port, debug=False)
        except Exception as e:
            print(f"ERREUR du serveur Flask: {e}")
    
    # Démarrer le serveur dans un thread démon
    try:
        server_thread = threading.Thread(target=run_server)
        server_thread.daemon = True
        server_thread.start()
        print(f"Serveur web démarré sur {local_url}")
        if public_url:
            print(f"URL publique accessible depuis Internet: {public_url}")
        return url
    except Exception as e:
        print(f"ERREUR lors du démarrage du thread serveur: {e}")
        return None