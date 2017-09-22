# JobFinder
Parser pour pole-emploi + Envoi de mail

Noter que chaque fichier PDF du dossier sera envoyé en pièce jointe du mail.


```
usage: JobFinder.py [-h] [-f] [-d [DEPARTEMENTS]] -k [KEYWORDS] [-t [TEST]]
                    [-s [SEND]]

optional arguments:
  -h, --help            show this help message and exit
  -f, --france          Recherche dans toute la France
  -d [DEPARTEMENTS], --departements [DEPARTEMENTS]
                        Recherche par département, eg: --departements
                        71,75,92,95
  -k [KEYWORDS], --keywords [KEYWORDS]
                        Mots clés à rechercher (recherche exclusive), eg:
                        --keywords PHP,python,java
  -t [TEST], --test [TEST]
                        Envoyer quelques mails de test à l'adresse indiquée,
                        eg: --test moi@domain.tld
  -s [SEND], --send [SEND]
                        Envoyer les mails à tous les destinataires de la base
                        d'adresses, eg: --send moi@gmail.com
```

Exemples :

```
# cherche les offres en Saône et Loire sur les mots clés PHP et Python, et envoie un mail de test à username
./JobFinder.py -d 71 -k PHP,python --test username@gmail.com 


# cherche les offres en France sur le mot clé "javascript", et envoie un mail de test à username
./JobFinder.py -f -k javascript --test username@gmail.com


# cherche les offres en France sur le mot clé "javascript", et envoie les mails à tous les contacts trouvés
./JobFinder.py -f -k javascript --send username@gmail.com
```
