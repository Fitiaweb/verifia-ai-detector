import requests
import json
import time

API_URL = "http://127.0.0.1:8000/api/analyze"

DATASET = [
    # ---- TEXTES IA (Expected: > 50) ----
    {
        "type": "IA",
        "text": "En résumé, il est important de noter que l'intelligence artificielle révolutionne de nombreux secteurs. Cependant, il convient de souligner que des défis éthiques persistent. En conclusion, nous devons aborder ces technologies avec précaution tout en exploitant leur potentiel."
    },
    {
        "type": "IA",
        "text": "Voici une liste des avantages du télétravail :\n- Flexibilité des horaires.\n- Réduction du temps de trajet.\n- Meilleur équilibre entre vie professionnelle et personnelle.\nEn fin de compte, il est primordial de mettre en place une communication efficace."
    },
    {
        "type": "IA",
        "text": "Absolument ! L'apprentissage automatique est une branche fascinante de l'informatique. Tout d'abord, il permet aux systèmes d'apprendre à partir de données. Ensuite, il optimise les processus de décision. Bien que cette technologie soit puissante, gardez à l'esprit qu'elle nécessite des données de haute qualité."
    },
    {
        "type": "IA",
        "text": "La révolution numérique a transformé nos habitudes. 1. Elle facilite l'accès à l'information. 2. Elle connecte les individus à l'échelle mondiale. En d'autres termes, nous vivons dans une ère d'interconnexion sans précédent. Il faut savoir que cela comporte aussi des risques."
    },
    {
        "type": "IA",
        "text": "Bien sûr, je peux vous aider avec ça. La blockchain est un registre distribué qui assure la transparence. Néanmoins, sa consommation énergétique fait débat. Il est essentiel de comprendre que chaque transaction est cryptée. En définitive, c'est une technologie disruptive."
    },
    # ---- TEXTES HUMAINS (Expected: < 50) ----
    {
        "type": "HUMAIN",
        "text": "Salut mec, on se voit toujours à 18h devant le bar ? J'ai grave hâte de te raconter ce qui s'est passé au boulot aujourd'hui, c'était un truc de fou. Mon boss a littéralement pété un câble en pleine réunion."
    },
    {
        "type": "HUMAIN",
        "text": "La lueur de la lune se reflétait doucement sur le lac gelé, créant une atmosphère presque magique. Jeanne resserra son écharpe autour de son cou, frissonnant malgré l'épais manteau de laine. Elle se demandait si ce voyage en valait vraiment la peine."
    },
    {
        "type": "HUMAIN",
        "text": "Je vous écris pour faire suite à notre entretien téléphonique de ce matin. Veuillez trouver ci-joint le dossier complété avec toutes les pièces justificatives demandées. N'hésitez pas à me recontacter s'il manque le moindre document."
    },
    {
        "type": "HUMAIN",
        "text": "Hier soir, je me suis fait un marathon de films d'horreur. Franchement, le dernier Conjuring m'a fait sursauter au moins trois fois. J'ai dû vérifier sous mon lit avant de dormir, tellement j'étais parano ! Bref, une super soirée mais je suis crevé aujourd'hui."
    },
    {
        "type": "HUMAIN",
        "text": "Le match d'hier était incroyable. L'équipe a montré une résilience folle après avoir été menée de deux buts en première mi-temps. La frappe en pleine lucarne à la 89ème minute restera dans les annales du club."
    }
]

# On multiplie par 1 pour tester rapidement
DATASET = DATASET * 1

def run_tests():
    print("Démarrage de la suite de tests...")
    
    # Créer ou connecter un utilisateur de test avec crédits
    session = requests.Session()
    headers = {}
    try:
        reg_res = session.post("http://127.0.0.1:8000/api/auth/register", json={
            "first_name": "Test",
            "last_name": "Runner",
            "birth_date": "2000-01-01",
            "email": f"testrunner_{int(time.time())}@test.com",
            "password": "Password123!"
        })
        if reg_res.status_code == 200:
            token = reg_res.json().get("token")
            headers["Authorization"] = f"Bearer {token}"
            # Créditer 20 tests pour le run
            session.get(f"http://127.0.0.1:8000/api/payments/confirm?email={reg_res.json().get('email')}&plan=pack_10&order_id=test_setup")
    except Exception as e:
        print(f"[TEST SETUP NOTE] Connexion locale directe: {e}")

    correct = 0
    total = len(DATASET)
    
    for i, item in enumerate(DATASET):
        print(f"\nTest {i+1}/{total} - Type attendu : {item['type']}")
        try:
            response = requests.post(API_URL, json={"text": item["text"]}, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                score = data.get("ai_probability", 0)
                source = data.get("source", "Inconnue")
                
                is_ai_detected = score >= 50
                expected_ai = (item["type"] == "IA")
                
                success = (is_ai_detected == expected_ai)
                if success:
                    correct += 1
                
                print(f"[{'SUCCESS' if success else 'FAIL'}] Score: {score}% | Source: {source}")
            else:
                print(f"[ERROR] Code HTTP: {response.status_code}")
        except Exception as e:
            print(f"[ERROR] Requête échouée: {e}")
            
        time.sleep(1) # Pause courte pour ne pas spammer
        
    accuracy = (correct / total) * 100
    print(f"\n=== RESULTATS : {accuracy}% de précision ({correct}/{total}) ===")

if __name__ == '__main__':
    run_tests()
