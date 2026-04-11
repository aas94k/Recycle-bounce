# 🌍 Recycle Bounce v2 — Le Flipper du Tri

**EarthTech · EFREI · TI250**  
BRIGUI Mohamed Amine · EL KAMEL Alaeddine · ABI SAAD Antoine

---

## Installation & Lancement

```bash
pip install pygame
python main.py
```

---

## Commandes

| Touche   | Action                      |
|----------|-----------------------------|
| `ESPACE` | Lancer la balle             |
| `←`      | Flipper gauche              |
| `→`      | Flipper droit               |
| `ÉCHAP`  | Retour au menu              |
| `R`      | Rejouer (écran game over)   |

---

## Fichiers

```
recycle_bounce/
├── main.py         ← Boucle principale + 3 écrans (Menu/Jeu/GameOver)
├── constants.py    ← Palette nature, config déchets, bumpers
├── draw_utils.py   ← Fond nature, fleurs-bumpers, poubelles cartoon
├── ball.py         ← Physique balle + trail + spin visuel
├── flipper.py      ← Flippers animés avec reflets
├── bin_target.py   ← 4 poubelles (Plastique, Papier, Verre, Bio)
└── assets/         ← Illustrations du projet
```

---

## Nouveautés v2 (redesign UI)

- ✅ **Fond nature animé** : collines, rivière sinueuse, arbres, fleurs
- ✅ **4 poubelles** avec couvercle, visage souriant, icône et couleurs maquette
- ✅ **Bumpers en fleurs** avec pétales et visage (style illustration)
- ✅ **Particules** colorées à chaque collision réussie
- ✅ **Carte "À trier"** repositionnée comme la maquette
- ✅ **Balle** avec spin visuel et glow lumineux
- ✅ **Flippers** avec reflets et ombre portée
- ✅ Menu immersif sur fond nature avec carte titre
