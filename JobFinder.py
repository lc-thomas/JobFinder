#!/usr/bin/env python3.4
# -*- coding: utf-8 -*-
try :
    import os, sys
    import argparse
    import datetime
    import requests
    from bs4 import BeautifulSoup
    import json
    import re
    import getpass
    import smtplib
    from email.mime.application import MIMEApplication
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    import time
except ImportError as e:
    print("[!] Vous n'avez pas les librairies nécessaires pour lancer ce programme.\n%s" % e)
    sys.exit()

class JobFinder():
    log_mode = {
        'info':'\033[94m[i]\033[0m',
        'success':'\033[92m[+]\033[0m',
        'error':'\033[91m[!]\033[0m',
    }
    htmlentities = {
        'é' : '&eacute;',
        'ê' : '&ecirc;',
        'è' : '&egrave;',
        'à' : '&agrave;',
        'â' : '&acirc;',
        'ï' : '&iuml;',
    }
    cache = []
    gmail_pass = False
    def __init__(self):
        self.log('Starting.')

    def log(self, message, mode = 'info'):
        now = datetime.datetime.now()
        c_time = now.strftime("%Y-%m-%d %H:%M:%S")
        print("%s %s [JobFinder] %s" % (self.log_mode[mode], c_time, message))

    def parse_args(self):
        self.log('Parsing args')
        parser = argparse.ArgumentParser(add_help = False)
        parser.add_argument('-f', '--france', help='Recherche dans toute la France', required=False, action='store_true')
        parser.add_argument('-d', '--departements', nargs='?', help='Recherche par département, eg: --departements 71,75,92,95', required=False)
        parser.add_argument('-k', '--keywords', nargs='?', help="Mots clés à rechercher (recherche exclusive), eg: --keywords PHP,python,java", required=True)
        parser.add_argument('-t', '--test', nargs='?', help="Envoyer quelques mails de test à l'adresse indiquée, eg: --test moi@domain.tld", required=False)
        parser.add_argument('-s', '--send', nargs='?', help="Envoyer les mails à tous les destinataires de la base d'adresses, eg: --send moi@gmail.com", required=False)
        parser.add_argument('-h', '--help', help="Afficher l'aide", required=False, action='store_true')
        self.args = parser.parse_args()
        if self.args.help:
            parser.print_help()
            self.exit()
        if not self.args.france and not self.args.departements:
            self.log("SVP veuillez renseigner la zone de recherche (eg : --france ou --departements 75,92,...)", 'error')
            parser.print_help()
            self.exit()
        if not self.args.keywords:
            self.log("SVP veuillez renseigner des mots clés à rechercher (eg : --keywords Python,Javascript)")
            parser.print_help()
            self.exit()

    def search_jobs(self):
        self.log('Finding your future job...')
        if self.args.france:
            lieux = ['01P']        
        else:
            lieux = [x.zfill(2)+"D" for x in self.args.departements.split(',')]
        with open('contacts.csv', 'w+') as f:
            for keyword in self.args.keywords.split(','):
                base_url = 'https://candidat.pole-emploi.fr/offres/recherche:afficherplusderesultats/[start]-1000?lieux=[LIEU]&motsCles=%s&offresPartenaires=false&rayon=100&tri=0' % keyword
                for lieu in lieux:
                    url = base_url.replace('[LIEU]', lieu)
                    has_results = True
                    start = 0
                    s = requests.Session()
                    while has_results:
                        currentUrl = url.replace('[start]', str(start))
                        offersJSON = s.get(currentUrl, headers={'X-Requested-With':'XMLHttpRequest'}).text
                        offersHTML = json.loads(offersJSON)['_tapestry']['content'][0][1:]
                        for offerHTML in offersHTML:
                            bs = BeautifulSoup(offerHTML, 'html.parser')
                            links = bs.findAll('a', {'class':'btn-reset'})
                            if not len(links): has_results = False
                            for link in links:
                                offer_id = link['href'].split('/')[-1]
                                if offer_id in self.cache:continue
                                if not link.has_attr('href'):continue
                                if link.find('span'):continue
                                self.cache.append(offer_id)
                                recruiter_name, recruiter_mail = self.get_offer_detail(offer_id)
                                if not recruiter_name or not recruiter_mail:continue

                                try :
                                    recruiter_mail = re.search(r'[\w\.-]+@[\w\.-]+', recruiter_mail).group(0)
                                except AttributeError as e:
                                    continue
                                try :
                                    entreprise, recruiter = tuple([x.strip() for x in recruiter_name.split('-')])
                                except ValueError as e:
                                    continue
                                line = "%s;%s;%s;%s" % (offer_id, entreprise, recruiter, recruiter_mail)
                                self.log(line, 'success')
                                f.write(line+"\n")      
                        start += 20
        self.log("Les annonces correspondant à vos critères ont bien été récupérées (contacts.csv)")
        
    def get_offer_detail(self, offer_id):
        detailHTML = requests.get('https://candidat.pole-emploi.fr/offres/recherche/detail/%s' % offer_id).text
        bs = BeautifulSoup(detailHTML, 'html.parser')
        try :
            dds = bs.find('div', {'class':'apply-block'}).findAll('dd')      
            return (cleanString(dds[0].decode_contents().split('<br/>')[0]), cleanString(dds[1].find('a').decode_contents()))
        except AttributeError as e:
            return (False, False)
        except IndexError as e:
            return (False, False)

    def send_mails(self):
        if not self.args.test and not self.args.send:
            self.log("Vous n'avez pas sélectionné de méthode d'envoi de mail (--send ou --test)", 'error')
            self.exit()            
        self.log("Préparation à l'envoi de mails")
        self.log("Les mails ne seront pas envoyés aux contacts déjà présents dans already_sent.csv, ni à un même destinataire")
        if self.args.test:
            gmail_login = self.args.test
            self.log("Envoi de mail à vous même, pour tester.")
        if self.args.send:
            gmail_login = self.args.send
            self.log("Envoi de mail aux contacts.")
            self.log("Etes vous sûr de bien vouloir envoyer les mails en utilisant le template (mail_template.html)? (O/N)")
            print('> Votre choix : ', end = "")
            v = input()
            if v.lower() in ['n', 'no', 'non'] or v.lower() not in ['o', 'oui', 'y', 'yes']:
                self.log("Okay pas d'envoi de mail.")
                self.exit()
        already_sent = []
        with open('already_sent.csv') as f:
            for line in f:
                already_sent.append(cleanString(line.split(';')[-1]))
        with open('contacts.csv') as f:
            max_test = 6
            i = 0
            with open('mail_template.html') as tpl:
                html = tpl.read()
            for key, val in self.htmlentities.items():
                html.replace(key, val)
            for line in f:
                offer_id = cleanString(line.split(';')[0])
                entreprise = cleanString(line.split(';')[1])
                contact = cleanString(line.split(';')[2])
                mail_to = cleanString(line.split(';')[3])
                if self.args.test:
                    mail_to = self.args.test
                    max_test -= 1
                    if max_test == 0:
                        self.log('Envoi des mails de test bien éffectué.')
                        self.exit()
                if mail_to in already_sent :
                    self.log('Un mail a déjà été envoyé à %s' % mail_to, 'error')
                    continue
                if self.gmail_pass == False:
                    self.log("Veuillez saisir votre mot de passe gmail. (Il n'est pas loggé - recommandation : Créez un compte gmail spécialement pour cet outil)")
                    self.gmail_pass = getpass.getpass('> Votre mot de passe gmail : ')
                if i % 80 == 0 or not gmail_server :
                    try :
                        gmail_server.close()
                    except UnboundLocalError as e:
                        pass
                    gmail_server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                    gmail_server.ehlo()
                    try :
                        gmail_server.login(gmail_login, self.gmail_pass)
                    except smtplib.SMTPAuthenticationError as e:
                        self.log('Wrong credentials', 'error')
                        self.log(e, 'error')
                        self.exit()
                    if i != 0:
                        self.log("[i] Resetting SMTP to avoid SPAM limit please wait...")
                        time.sleep(15)
                html2 = html
                html2 = html2.replace('[DEST]', contact)
                html2 = html2.replace('[URL_ANNONCE]', 'https://candidat.pole-emploi.fr/offres/recherche/detail/%s' % offer_id)
                msg = MIMEMultipart()
                msg.attach(MIMEText(html2, 'html'))
                for file in os.listdir('.'):
                    if file.endswith('.pdf'):
                        with open(file, 'rb') as cv:
                            part = MIMEApplication(cv.read(), Name=file)
                            part['Content-Disposition'] = 'attachment; filename="%s"' % file
                            msg.attach(part)
                msg['Subject'] = "Offre d'emploi %s" % offer_id
                msg['From'] = gmail_login
                msg['To'] = mail_to
                self.log("Envoi d'un mail à %s (%s) - Offre %s" % (contact, mail_to, offer_id))
                i+=1
                try :
                    gmail_server.sendmail(gmail_login, mail_to, msg.as_string())
                except smtplib.SMTPRecipientsRefused as e:
                    self.log("Adresse TO invalide : %s" % e, "error")
                time.sleep(3)
                if not self.args.test:
                    with open('already_sent.csv', 'a+') as asent:
                        asent.write('%s\n' % line)
                    already_sent.append(mail_to)
        self.log('%s mails envoyés !' % i, 'success')
        self.exit()

    def exit(self):
        self.log('Exiting.')
        sys.exit()


def cleanString(st):
    return st.replace('\n', '').replace('\r', '').replace('<br/>','').strip()

if __name__ == '__main__':
    jf = JobFinder()
    jf.parse_args()
    jf.search_jobs()
    jf.send_mails()
    jf.exit()