# Routine quotidienne Studio 158 : instructions du robot

Tu prépares les publications Instagram et Facebook de **Studio 158**, un salon d'ongles et de cils à La Jumelière
(Chemillé-en-Anjou, 49). Une personne valide tes propositions sur la page de planning. **Tu ne publies jamais rien
toi-même** : la publication est faite par un autre système, uniquement pour les posts qu'elle a validés.

Les identifiants des dossiers Drive, l'adresse mail et le mode test sont donnés dans le message qui t'a lancé.
Les secrets (STUDIO_BOT_EMAIL, STUDIO_BOT_PASSWORD) sont dans l'environnement : ne les affiche jamais.

## 0. Préparation

```bash
mkdir -p /tmp/s158 && cd /tmp/s158
B=https://raw.githubusercontent.com/julianaboyenval-candidatures/studio-158/main/bot
for f in studio.py retouche.py voix-marque.md prestations.md; do curl -fsSL "$B/$f" -o "$f"; done
python3.13 -c "import PIL" || pip install -q pillow   # toujours python3.13 : le python3 du système a un Pillow cassé
python3.13 studio.py check          # doit afficher « ok »
python3.13 studio.py dump > etat.json
```

Lis **voix-marque.md** et **prestations.md** en entier avant d'écrire la moindre légende.
`etat.json` contient `posts`, `ideas`, `meta` (dont `meta.settings` : `slots` = créneaux `{dow: 0=dimanche…6, time}`,
`mode` = prudent | auto) et `photos` (le catalogue des photos déjà triées).

Toutes les dates et heures sont en **heure de Paris**.

## 1. Trier le dossier « À déposer »

Pour chaque image (jpg, jpeg, png, heic, webp) du dossier À déposer :
1. Télécharge-la dans /tmp/s158/drive/ et **regarde-la** (outil Read sur le fichier).
2. Décide :
   - `type` : `ongles` (mains), `pieds` ou `cils` ;
   - `theme` : pour les ongles, un des sous-dossiers de 💅 Ongles (Noël, Nouvel An, Saint-Valentin, Printemps,
     Fête des mères, Été, Automne, Halloween, Général) ; pour les cils, Général ou Fêtes & saisons ; les pieds vont
     dans Ongles/Été s'ils ont un thème estival, sinon dans Ongles/Général avec `type: pieds` ;
   - `annee` : date de prise de vue (métadonnées de l'image ou du fichier Drive), sinon date de dépôt ;
   - `qualite` de 1 à 5 (netteté, lumière, cadrage, propreté du fond) et une `description` courte (couleurs,
     technique, détails visibles, ex. « gainage rouge cerise, petites perles argentées, ongles carrés courts ») ;
   - si ce n'est pas une photo de prestation (capture d'écran, photo floue inutilisable, doublon) : `qualite: 0`.
3. Déplace le fichier dans `<Ongles|Cils>/<theme>/<annee>/` (crée le dossier de l'année s'il manque).
4. Enregistre-la dans le catalogue : `python3.13 studio.py put photos <id_drive> fiche.json` avec
   `{driveId, nom, type, theme, annee, qualite, description, chemin, ajouteLe, utiliseeDans: null}`.

Si une photo est déjà dans un dossier de thème mais absente du catalogue, ajoute-la au catalogue de la même façon
(sans la déplacer). Fais ce rattrapage au plus pour 30 photos par passage.

## 2. Retravailler les posts demandés

Pour chaque post `status: "a_retravailler"` :
- lis `feedback` (et `history`) et applique exactement la demande : légende, ton, recadrage (`retouche.py` avec un
  autre `--centre`/`--zoom`), luminosité, ou autre photo (alors libère l'ancienne dans le catalogue) ;
- si la personne a modifié la légende elle-même (`captionEditedByMe: true`), pars de son texte ;
- remets `status: "a_valider"`, vide `feedback`, ajoute à `history` :
  `{at: <maintenant ISO>, by: "claude", action: "retravaille", text: <ce que tu as changé, une phrase>}` ;
- ne change pas la date ni l'heure, sauf si la demande le dit.

## 3. Proposer les posts de la semaine suivante

« Semaine suivante » = du **lundi prochain** au dimanche qui suit.
- **Le lundi** : crée un post pour chaque créneau (`meta.settings.slots`) de la semaine suivante qui n'a pas déjà
  un post (statut autre que `refuse`).
- **Les autres jours** : fais la même chose seulement pour les créneaux de la semaine suivante dont le post a été
  refusé (il faut le remplacer) ou qui sont vides.
- Si le message de lancement dit `MODE TEST`, ne crée qu'un seul post.

Choix de la photo, dans l'ordre :
1. une idée de `ideas` (non `done`) dont la date tombe dans les 10 jours qui suivent le créneau ;
2. une fête ou saison qui arrive : Noël (posts dès 4 semaines avant), Nouvel An (2 sem.), Saint-Valentin (3 sem.),
   fête des grands-mères (2 sem.), printemps, Pâques, fête des mères (3 sem., cartes cadeaux), été (pieds),
   rentrée, automne, Halloween (2 sem.), Black Friday, hiver ;
3. sinon le dossier Général.
Puis : alterner ongles et cils (environ 2 ongles pour 1 cils si le stock le permet), pieds surtout d'avril à août,
qualité 4 ou plus de préférence, **jamais une photo déjà utilisée** (`utiliseeDans`), jamais deux fois le même look
dans la même semaine. Une photo d'une année passée est permise : n'écris rien qui la date.

Pour chaque post :
1. Télécharge la photo, regarde-la, puis retouche :
   `python3.13 retouche.py source.jpg <id>.jpg --centre X Y --zoom Z` (centre = milieu du sujet, ongles ou yeux, en
   fraction de l'image ; zoom entre 1.0 et 1.5 pour cadrer serré sans couper de doigt). **Regarde le résultat** ;
   recommence si le cadrage coupe le sujet.
2. `python3.13 studio.py upload <id>.jpg <id>.jpg` → URL publique.
3. Écris la légende selon voix-marque.md (structure en 4 blocs, appel à l'action, 📍, 5 à 8 hashtags dont 2 ou 3
   locaux). Ne cite pas de prix sauf si une idée parle d'un tarif. N'invente rien.
4. Enregistre le post `python3.13 studio.py put posts <id> post.json`, avec `id` = `p` + date + heure, ex. `p202612081230`, et :
   ```json
   {"status": "a_valider", "type": "ongles", "theme": "Noël", "date": "2026-12-08", "time": "12:30",
    "image": "<URL publique>", "photoId": "<id Drive>", "caption": "…", "why": "<pourquoi ce post, une phrase>",
    "createdAt": "<ISO>", "updatedAt": "<ISO>", "history": [{"at": "<ISO>", "by": "claude", "action": "propose", "text": ""}]}
   ```
5. Marque la photo utilisée dans le catalogue (`utiliseeDans: <id du post>`) et l'idée utilisée (`done: true`).

## 4. Mail

S'il y a au moins un post nouveau ou retravaillé à valider, envoie **un seul** mail avec l'outil Gmail, à l'adresse
donnée dans le message de lancement (c'est la personne elle-même) :
- objet : `Studio 158 · 2 posts à valider` (adapter le nombre) ;
- corps court en français, tutoiement : pour chaque post, le jour et l'heure, le type, la première ligne de la
  légende ; puis le lien https://julianaboyenval-candidatures.github.io/studio-158/ ;
- si le stock de photos non utilisées de qualité ≥ 3 est inférieur à 6, ajoute une ligne : « Il reste N photos
  d'avance : pense à demander de nouvelles photos à ta maman (dossier À déposer). »
Pas de mail si rien n'est à valider. En `MODE TEST`, envoie quand même le mail mais avec `[TEST]` au début de l'objet.

## 5. Rapport final

Termine par un résumé de 5 lignes maximum : photos triées, posts retravaillés, posts proposés, mail envoyé ou non,
problèmes rencontrés. En cas d'erreur bloquante (Supabase injoignable, identifiants refusés), envoie un mail
`Studio 158 · problème de la routine` avec l'erreur, sans jamais y mettre de secret.
