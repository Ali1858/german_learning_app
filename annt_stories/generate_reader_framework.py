#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scalable generator for the German A2 -> B1 case + gender story reader.

This is SOURCE, not a wrapper around finished HTML.

The course lives in STORIES as structured Python data. The renderer below
creates all HTML, navigation, indexes, vocabulary popovers, case/gender
formatting, recall blocks, CSS and JavaScript.

Annotation syntax used inside story paragraphs
----------------------------------------------
Gender-only noun:
    <<m|Tisch>>        <<f|Wohnung>>        <<n|Fenster>>

Case phrase:
    {{nom|m|d[er] alt[e]|Mann}}
    {{akk|m|d[en] alt[en]|Mann}}
    {{dat|m|d[em] alt[en]|Mann}}

Text inside [square brackets] is an ending cue. The renderer makes it
BOLD + the color of the phrase's case.

Case trigger:
    [[akk|sehen]]
    [[dat|mit]]

B1 bridge word:
    ((obwohl|although))

How to scale
------------
1. Append another dictionary to STORIES.
2. Give it a sequential "number", a title, target nouns, paragraphs,
   B1 bridge words and recall questions.
3. Run this script. Navigation and indexes are rebuilt automatically.
4. validate_course() catches duplicate target nouns, missing glosses,
   bad gender codes and numbering errors.

Usage:
    python generate_reader_framework.py
    python generate_reader_framework.py my_reader.html
"""

from pathlib import Path
import sys
import re
import html

GENDER_COLORS = {"m":"#2563eb","f":"#be123c","n":"#15803d"}
CASE_COLORS = {"nom":"#0f766e","akk":"#7c3aed","dat":"#d97706"}
ARTICLES = {"m":"der","f":"die","n":"das"}

STORIES = [{'number': 1,
  'title': 'Einzug in die neue Wohnung',
  'targets': [('f', 'Wohnung', 'apartment'),
              ('m', 'Umzug', 'move'),
              ('m', 'Karton', 'box'),
              ('m', 'Schlüssel', 'key'),
              ('f', 'Tür', 'door'),
              ('n', 'Fenster', 'window'),
              ('n', 'Zimmer', 'room'),
              ('f', 'Küche', 'kitchen'),
              ('n', 'Bad', 'bathroom'),
              ('m', 'Tisch', 'table'),
              ('m', 'Stuhl', 'chair'),
              ('n', 'Bett', 'bed'),
              ('m', 'Schrank', 'wardrobe/cabinet'),
              ('f', 'Lampe', 'lamp'),
              ('n', 'Regal', 'shelf'),
              ('m', 'Teppich', 'carpet'),
              ('f', 'Tasche', 'bag'),
              ('m', 'Koffer', 'suitcase'),
              ('m', 'Nachbar', 'male neighbor'),
              ('f', 'Nachbarin', 'female neighbor'),
              ('m', 'Vermieter', 'landlord'),
              ('f', 'Adresse', 'address'),
              ('m', 'Stock', 'floor/storey'),
              ('f', 'Treppe', 'stairs'),
              ('m', 'Aufzug', 'elevator')],
  'paragraphs': ['Samir zieht [[dat|an]] {{dat|m|ein[em]|Samstag}} um. {{nom|m|d[er] groß[e]|Umzug}} beginnt früh, '
                 'und [[dat|vor]] {{dat|n|d[em]|Haus}} stehen {{nom|m|viel[e]|Kartons}}. {{nom|m|d[er] '
                 'freundlich[e]|Nachbar}} Karim [[akk|trägt]] {{akk|m|ein[en] schwer[en]|Karton}} [[dat|zu]] '
                 '{{dat|m|d[em] neu[en]|Vermieter}}. Samir [[akk|sucht]] {{akk|m|d[en] klein[en]|Schlüssel}}, weil '
                 'er {{akk|f|d[ie]|Tür}} nicht [[akk|öffnen]] kann. Schließlich findet er ihn [[dat|in]] '
                 '{{dat|f|sein[er] blau[en]|Tasche}}.',
                 '{{nom|f|D[ie] hell[e]|Wohnung}} liegt [[dat|im]] {{dat|m|dritt[en]|Stock}}. Samir [[akk|nimmt]] '
                 'zuerst {{akk|f|d[ie]|Treppe}}; später [[akk|benutzt]] er auch {{akk|m|d[en]|Aufzug}}. In '
                 '{{dat|n|d[em] erst[en]|Zimmer}} stehen {{nom|m||Tisch}}, {{nom|m||Stuhl}}, {{nom|n||Bett}}, '
                 '{{nom|m||Schrank}}, {{nom|f||Lampe}}, {{nom|n||Regal}} und {{nom|m||Teppich}}. Er [[akk|stellt]] '
                 '{{akk|f|d[ie] neu[e]|Lampe}} [[dat|neben]] {{dat|n|d[as] groß[e]|Fenster}}. Danach [[akk|legt]] '
                 'er {{akk|m|d[en] weich[en]|Teppich}} [[dat|vor]] {{dat|n|d[as] klein[e]|Bett}}.',
                 'Später kommt {{nom|f|d[ie] nett[e]|Nachbarin}} vorbei. Sie [[akk|zeigt]] Samir {{akk|f|d[ie]|Küche}} '
                 'und {{akk|n|d[as]|Bad}}. Samir [[akk|stellt]] {{akk|m|d[en] braun[en]|Koffer}} [[dat|in]] '
                 '{{dat|n|d[as] frei[e]|Zimmer}} und [[akk|hängt]] {{akk|m|ein[en]|Zettel}} [[dat|mit]] '
                 '{{dat|f|sein[er]|Adresse}} [[akk|an]] {{akk|f|d[ie]|Tür}}. '
                 '((Obwohl|although)) noch nicht alles fertig ist, fühlt sich {{nom|f|d[ie]|Wohnung}} schon wie ein '
                 'Zuhause an.',
                 '[[dat|Am]] {{dat|m||Sonntag}} [[akk|packt]] Samir {{akk|m|d[ie] restlich[en]|Kartons}} aus.\n'
                 'Er [[akk|räumt]] {{akk|f|d[ie]|Küche}} auf, [[akk|wischt]] {{akk|m|d[en]|Boden}}\n'
                 'und [[akk|hängt]] {{akk|n|zwei|Bilder}} [[akk|an]] {{akk|f|d[ie]|Wand}}.\n'
                 'Karim kommt noch einmal vorbei und [[dat|hilft]] {{dat|m|d[em] neu[en]|Mieter}} [[dat|beim]] '
                 '{{dat|m||Aufbau}} eines <<n|Regals>>.\n'
                 'Danach wirkt {{nom|n|d[as]|Zimmer}} heller und gemütlicher.\n'
                 '{{nom|f|D[ie] neu[e]|Ordnung}} ist auch praktisch: {{nom|m||Schlüssel}}, {{nom|m||Briefe}} und '
                 '{{nom|n||Werkzeug}} haben jetzt {{akk|m|ein[en] fest[en]|Platz}}.\n'
                 'Samir arbeitet ordentlich, aber nicht perfekt. Vermutlich [[akk|braucht]] er noch ein paar '
                 '{{akk|m||Tage}}.\n'
                 'Er [[akk|kocht]] gleichzeitig {{akk|m||Kaffee}} und [[akk|nutzt]] {{akk|f|d[ie]|Gelegenheit}}, '
                 '{{akk|f|d[ie]|Nachbarin}} [[akk|auf]] {{akk|m|ein[en]|Kaffee}} einzuladen.'],
  'b1': ['gemütlich', 'praktisch', 'ordentlich', 'vermutlich', 'gleichzeitig', 'Gelegenheit'],
  'recall': [('Warum heißt es „mit seiner blauen Tasche“?',
              'Weil „mit“ den Dativ verlangt; „Tasche“ ist feminin → mit seiner blauen Tasche.'),
             ('Welche Form passt: ___ neuen Vermieter?', 'zu dem neuen Vermieter / zum neuen Vermieter.'),
             ('Akkusativ von „der kleine Schlüssel“?', 'den kleinen Schlüssel.'),
             ('Dativ von „das große Fenster“?', 'dem großen Fenster.'),
             ('Welche Farbe bleibt am Nomen „Teppich“ gleich?', 'Blau, weil „Teppich“ maskulin ist.')]},
 {'number': 2,
  'title': 'Der erste Weg durch das Viertel',
  'targets': [('f', 'Straße', 'street'),
              ('f', 'Ecke', 'corner'),
              ('f', 'Bäckerei', 'bakery'),
              ('m', 'Supermarkt', 'supermarket'),
              ('m', 'Markt', 'market'),
              ('f', 'Apotheke', 'pharmacy'),
              ('f', 'Bank', 'bank'),
              ('f', 'Post', 'post office/mail'),
              ('m', 'Park', 'park'),
              ('m', 'Spielplatz', 'playground'),
              ('f', 'Bushaltestelle', 'bus stop'),
              ('m', 'Bahnhof', 'train station'),
              ('n', 'Fahrrad', 'bicycle'),
              ('m', 'Bus', 'bus'),
              ('n', 'Auto', 'car'),
              ('f', 'Ampel', 'traffic light'),
              ('f', 'Kreuzung', 'intersection'),
              ('f', 'Brücke', 'bridge'),
              ('m', 'Fluss', 'river'),
              ('f', 'Kirche', 'church'),
              ('n', 'Rathaus', 'town hall'),
              ('f', 'Polizei', 'police'),
              ('m', 'Laden', 'shop'),
              ('m', 'Kiosk', 'kiosk'),
              ('m', 'Weg', 'way/path')],
  'paragraphs': ['[[dat|Am]] {{dat|m|nächst[en]|Morgen}} [[akk|erkundet]] Samir {{akk|n|sein|Viertel}}. {{nom|f|D[ie] '
                 'ruhig[e]|Straße}} führt [[dat|zu]] '
                 '{{dat|f|ein[er] groß[en]|Kreuzung}}. [[dat|An]] {{dat|f|d[er]|Ecke}} liegt {{nom|f|ein[e]|Bäckerei}}, daneben '
                 '{{nom|m|ein|Supermarkt}} und gegenüber {{nom|f|ein[e]|Apotheke}}. Samir [[akk|überquert]] {{akk|f|d[ie] '
                 'breit[e]|Kreuzung}} [[dat|bei]] {{dat|f|d[er] grün[en]|Ampel}}.',
                 'Er [[akk|kauft]] {{akk|n|ein neu[es]|Fahrrad}} [[dat|bei]] {{dat|m|ein[em] klein[en]|Laden}}. Danach '
                 'fährt er [[akk|durch]] {{akk|m|d[en]|Park}}, [[dat|an]] {{dat|m|d[em]|Spielplatz}} vorbei und weiter '
                 '[[dat|zum]] {{dat|m||Fluss}}. {{nom|f|D[ie] alt[e]|Brücke}} [[akk|verbindet]] {{akk|m|zwei|Teile}} des Viertels. [[dat|Von]] '
                 '{{dat|f|d[er]|Brücke}} [[akk|sieht]] Samir {{akk|f|d[ie]|Kirche}}, {{akk|n|d[as]|Rathaus}} und {{akk|m|ein[en] '
                 'klein[en]|Kiosk}}.',
                 '[[dat|Am]] {{dat|m||Bahnhof}} wartet bereits {{nom|m|ein|Bus}}. Samir [[akk|nimmt]] {{akk|m|d[en] nächst[en]|Bus}} '
                 '[[dat|von]] {{dat|f|d[er] zentral[en]|Bushaltestelle}} zurück nach Hause. Unterwegs [[akk|sieht]] er '
                 '{{akk|f|d[ie]|Bank}}, {{akk|f|d[ie]|Post}}, {{akk|m|d[en]|Markt}}, {{akk|f|d[ie]|Polizei}} und {{akk|n|ein parkend[es]|Auto}}. '
                 '((Deshalb|therefore)) kennt er [[dat|am]] {{dat|m||Abend}} schon {{akk|m|viel[e]|Wege}} und muss nicht mehr ständig '
                 '[[akk|auf]] {{akk|m|d[en]|Stadtplan}} schauen.',
                 '[[dat|Am]] {{dat|m||Dienstag}} probiert Samir {{akk|m|ein[en] ander[en]|Weg}} [[dat|zur]] {{dat|f||Arbeit}}.\n'
                 '[[akk|Für]] {{akk|f|d[ie]|Orientierung}} schaut er kurz [[akk|auf]] {{akk|f|d[ie]|Karte}}, dann geht '
                 'er [[akk|ohne]] {{akk|n||Handy}} weiter.\n'
                 'Morgens ist {{nom|m|d[er]|Verkehr}} stärker als [[dat|am]] {{dat|m||Sonntag}}.\n'
                 '[[dat|An]] {{dat|f|ein[er]|Kreuzung}} fragt ihn {{nom|m|ein|Radfahrer}} [[dat|nach]] {{dat|f|d[er]|Richtung}} '
                 '[[dat|zum]] {{dat|m||Bahnhof}}.\n'
                 'Samir kann schon helfen. Einmal spricht er kurz [[dat|mit]] {{dat|f|d[er]|Polizei}} [[akk|über]] {{akk|m|d[en]|Weg}}. '
                 'Fast alles [[dat|im]] {{dat|n||Viertel}} ist zu Fuß erreichbar.\n'
                 'Inzwischen kennt er auch {{akk|f|d[ie] ruhig[en]|Straßen}} [[dat|in]] {{dat|f|d[er]|Umgebung}}.\n'
                 'Er [[akk|überquert]] {{akk|f|d[ie] schmal[e]|Brücke}}, wartet [[dat|an]] {{dat|f|d[er]|Ampel}}\n'
                 'und steigt später [[akk|in]] {{akk|m|d[en]|Bus}} ein.\n'
                 '[[dat|Am]] {{dat|m||Abend}} [[akk|erklärt]] er Lena {{akk|m|d[en]|Weg}}, ohne [[akk|auf]] {{akk|m|d[en]|Stadtplan}} zu sehen.'],
  'b1': ['Orientierung', 'Verkehr', 'Richtung', 'erreichbar', 'inzwischen', 'Umgebung'],
  'recall': [('Was triggert den Dativ in „bei der grünen Ampel“?', 'Die Präposition „bei“.'),
             ('Akkusativ von „der nächste Bus“?', 'den nächsten Bus.'),
             ('Dativ von „die zentrale Bushaltestelle“?', 'der zentralen Bushaltestelle.'),
             ('Warum ist „Fahrrad“ grün markiert?', 'Weil „das Fahrrad“ neutrum ist.'),
             ('Welche Präposition steht immer mit Dativ: durch oder von?', 'von.')]},
 {'number': 3,
  'title': 'Der erste Arbeitstag',
  'targets': [('f', 'Arbeit', 'work'),
              ('n', 'Büro', 'office'),
              ('f', 'Firma', 'company'),
              ('m', 'Chef', 'male boss'),
              ('f', 'Chefin', 'female boss'),
              ('m', 'Kollege', 'male colleague'),
              ('f', 'Kollegin', 'female colleague'),
              ('m', 'Termin', 'appointment'),
              ('f', 'Sitzung', 'meeting'),
              ('f', 'Aufgabe', 'task'),
              ('n', 'Projekt', 'project'),
              ('m', 'Computer', 'computer'),
              ('m', 'Bildschirm', 'screen'),
              ('f', 'Tastatur', 'keyboard'),
              ('f', 'Maus', 'mouse'),
              ('m', 'Drucker', 'printer'),
              ('n', 'Dokument', 'document'),
              ('f', 'E-Mail', 'email'),
              ('f', 'Nachricht', 'message'),
              ('n', 'Telefon', 'telephone'),
              ('m', 'Kalender', 'calendar'),
              ('f', 'Pause', 'break'),
              ('f', 'Kantine', 'cafeteria'),
              ('m', 'Vertrag', 'contract'),
              ('n', 'Gehalt', 'salary')],
  'paragraphs': ['Montag beginnt {{nom|f|d[ie] neu[e]|Arbeit}} [[dat|in]] {{dat|f|ein[er] klein[en]|Firma}}. '
                 '{{nom|f|D[ie] freundlich[e]|Chefin}} [[akk|begrüßt]] Samir und [[akk|zeigt]] ihm {{akk|n|d[as]|Büro}}. '
                 '[[dat|Auf]] {{dat|m|d[em]|Tisch}} stehen {{nom|m|ein|Computer}}, {{nom|m|ein|Bildschirm}}, '
                 '{{nom|f|ein[e]|Tastatur}}, {{nom|f|ein[e]|Maus}} und {{nom|n|ein|Telefon}}. '
                 'Samir [[akk|öffnet]] {{akk|n|d[as] erst[e]|Dokument}} [[dat|mit]] {{dat|f|d[er] neu[en]|Maus}}.',
                 'Kurz danach kommt {{nom|m|ein|Kollege}} [[dat|mit]] {{dat|f|ein[er]|Kollegin}}. Gemeinsam sprechen sie '
                 '[[akk|über]] {{akk|n|ein|Projekt}}, {{akk|f|ein[e]|Aufgabe}} und {{akk|m|ein[en]|Termin}}. Samir [[akk|trägt]] '
                 '{{akk|m|d[en] wichtig[en]|Termin}} [[dat|in]] {{dat|m|d[en] digital[en]|Kalender}} ein. [[dat|Vor]] '
                 '{{dat|f|d[er]|Sitzung}} [[akk|liest]] er {{akk|f|ein[e]|E-Mail}} und [[akk|beantwortet]] {{akk|f|ein[e]|Nachricht}}. '
                 '{{nom|m|D[er]|Drucker}} macht kurz Probleme, aber {{nom|m|ein|Kollege}} hilft.',
                 '[[dat|In]] {{dat|f|d[er]|Pause}} gehen alle [[akk|in]] {{akk|f|d[ie]|Kantine}}. Dort [[akk|erklärt]] '
                 '{{nom|f|d[ie]|Chefin}} {{akk|m|d[en]|Vertrag}} und {{akk|n|d[as]|Gehalt}} noch einmal. Kurz darauf grüßt auch {{nom|m|d[er] '
                 'gut gelaunt[e]|Chef}} der ganzen Firma. ((Während|while)) des Gesprächs merkt '
                 'Samir, dass er viel versteht, auch wenn einige Wörter neu sind. [[dat|Am]] {{dat|n||Ende}} des Tages [[akk|legt]] er '
                 '{{akk|n|d[as] unterschrieben[e]|Dokument}} [[dat|auf]] {{dat|m|d[em] frei[en]|Tisch}} und geht '
                 'zufrieden nach Hause.',
                 '[[dat|Nach]] {{dat|m|einig[en]|Tagen}} [[akk|bekommt]] Samir {{akk|f|mehr|Verantwortung}}.\n'
                 '{{nom|f|Sein[e] erst[e]|Erfahrung}} [[dat|mit]] {{dat|n|d[em]|Projekt}} ist positiv, weil die '
                 'Kollegen zuverlässig arbeiten.\n'
                 'Er muss {{akk|f|mehrere klein[e]|Aufgaben}} [[akk|erledigen]], {{akk|f|ein[e]|Datei}} schicken und '
                 '[[akk|auf]] {{akk|f|ein[e]|Rückmeldung}} warten.\n'
                 'Am Nachmittag darf er [[dat|an]] {{dat|f|ein[er] zweit[en]|Sitzung}} teilnehmen.\n'
                 'Danach [[dat|dankt]] er {{dat|m|d[em]|Chef}} [[akk|für]] {{akk|n|d[as] freundlich[e]|Gespräch}}.\n'
                 'Vorher [[akk|liest]] er {{akk|m|d[en] kurz[en]|Vertrag}} noch einmal und spricht [[dat|mit]] '
                 '{{dat|f|sein[er]|Chefin}} [[akk|über]] {{akk|f|offen[e]|Fragen}}.\n'
                 'Er [[akk|schreibt]] {{akk|f||Notizen}}, [[akk|druckt]] {{akk|f|zwei|Seiten}} aus und telefoniert [[dat|mit]] {{dat|m|ein[em]|Kunden}}.\n'
                 'Als {{nom|m|d[er]|Arbeitstag}} endet, ist Samir müde, aber zufrieden: Er [[akk|versteht]] {{akk|m|d[ie]|Abläufe}} schon '
                 'deutlich besser.'],
  'b1': ['Verantwortung', 'Erfahrung', 'zuverlässig', 'erledigen', 'Rückmeldung', 'teilnehmen'],
  'recall': [('Dativ nach „mit“: ___ neuen Maus', 'mit der neuen Maus.'),
             ('Akkusativ: ___ wichtigen Termin', 'den wichtigen Termin.'),
             ('Warum ist „Chefin“ feminin?',
              'Das Nomen ist „die Chefin“; der Nomenstamm bleibt feminin in allen Fällen.'),
             ('Was triggert „dem freien Tisch“?', 'Hier die Wechselpräposition „auf“ mit Ort (Wo?) → Dativ.'),
             ('Nominativ von „die neue Arbeit“?', 'die neue Arbeit.')]},
 {'number': 4,
  'title': 'Kleidung für den Herbst',
  'targets': [('m', 'Einkauf', 'shopping'),
              ('n', 'Geschäft', 'shop/business'),
              ('n', 'Kaufhaus', 'department store'),
              ('m', 'Verkäufer', 'salesman'),
              ('f', 'Verkäuferin', 'saleswoman'),
              ('m', 'Kunde', 'male customer'),
              ('f', 'Kundin', 'female customer'),
              ('m', 'Preis', 'price'),
              ('n', 'Angebot', 'offer'),
              ('f', 'Kasse', 'checkout/cash desk'),
              ('f', 'Rechnung', 'bill/invoice'),
              ('n', 'Geld', 'money'),
              ('f', 'Karte', 'card/map'),
              ('f', 'Größe', 'size'),
              ('f', 'Farbe', 'color'),
              ('n', 'Hemd', 'shirt'),
              ('f', 'Hose', 'trousers'),
              ('f', 'Jacke', 'jacket'),
              ('n', 'Kleid', 'dress'),
              ('m', 'Schuh', 'shoe'),
              ('f', 'Socke', 'sock'),
              ('m', 'Pullover', 'sweater'),
              ('m', 'Mantel', 'coat'),
              ('m', 'Gürtel', 'belt'),
              ('f', 'Mütze', 'cap/beanie')],
  'paragraphs': ['[[dat|Nach]] {{dat|f|d[er]|Arbeit}} macht Samir {{akk|m|ein[en]|Einkauf}}. {{nom|n|D[as] groß[e]|Kaufhaus}} hat {{akk|f|mehrere|Etagen}}, aber er beginnt [[dat|in]] {{dat|n|ein[em] klein[en]|Geschäft}}. {{nom|f|D[ie] '
                 'freundlich[e]|Verkäuferin}} [[akk|zeigt]] ihm {{akk|n||Hemd}}, {{akk|f||Hose}}, {{akk|f||Jacke}}, {{akk|n||Kleid}}, '
                 '{{akk|m||Pullover}}, {{akk|m||Mantel}}, {{akk|m||Gürtel}} und {{akk|f||Mütze}} [[dat|in]] {{dat|f|verschieden[en]|Farben}}.',
                 'Samir [[akk|probiert]] {{akk|m|ein[en] dunkel[en]|Pullover}} [[dat|mit]] {{dat|f|ein[er] '
                 'grau[en]|Hose}} an. Danach [[akk|vergleicht]] er {{akk|m|d[en]|Preis}} [[dat|mit]] '
                 '{{dat|n|ein[em]|Angebot}}. {{nom|f|Ein[e]|Kundin}} [[akk|sucht]] {{akk|f|ihr[e]|Größe}}, während {{nom|m|ein|Verkäufer}} '
                 '{{dat|m|ein[em]|Kunden}} {{akk|m|neu[e]|Schuhe}} und {{akk|f||Socken}} bringt. Samir entscheidet sich [[akk|für]] '
                 '{{akk|f|ein[e]|Jacke}}.',
                 '[[dat|An]] {{dat|f|d[er]|Kasse}} [[akk|bezahlt]] er {{akk|f|d[ie] neu[e]|Jacke}} [[dat|mit]] {{dat|f|sein[er] '
                 'Bank-|Karte}}. Er [[akk|bekommt]] {{akk|f|ein[e]|Rechnung}} und [[akk|steckt]] {{akk|n|d[as] übrig[e]|Geld}} [[akk|in]] {{akk|f|d[ie]|Geldbörse}}. '
                 '((Trotzdem|nevertheless)) schaut er noch einmal [[dat|nach]] {{dat|f|ein[er] warm[en]|Mütze}}, weil '
                 '{{nom|m|d[er]|Herbst}} bald kälter wird.',
                 '{{akk|f|Ein[e]|Woche}} später merkt Samir, dass {{nom|f|ein[e]|Hose}} nicht richtig passt.\n'
                 'Er geht [[dat|mit]] {{dat|f|d[er]|Rechnung}} zurück [[akk|ins]] {{akk|n||Geschäft}}.\n'
                 '{{nom|f|D[ie]|Verkäuferin}} [[akk|erklärt]] {{akk|f|d[ie]|Qualität}} der verschiedenen Stoffe und '
                 '[[akk|zeigt]] {{akk|f|ein[e] größer[e]|Auswahl}}.\n'
                 'Samir darf {{akk|f|d[ie]|Hose}} [[akk|umtauschen]]. Jedenfalls [[akk|findet]] er schnell {{akk|n|ein '
                 'passend[es]|Modell}}.\n'
                 '{{nom|m|Ein ander[er]|Kunde}} wartet ebenfalls [[dat|an]] {{dat|f|d[er]|Kasse}}. {{nom|f|D[ie]|Farbe}} gefällt ihm '
                 'sofort, und auch {{nom|m|d[er]|Schuh}} dazu passt gut. Nur {{nom|f|ein[e]|Socke}} hat schon ein '
                 'kleines Loch.\n'
                 'Er [[akk|vergleicht]] {{akk|m|zwei|Preise}}, [[akk|probiert]] {{akk|f|drei|Größen}} an und entscheidet sich [[akk|für]] {{akk|f|d[ie] '
                 'bequemer[e]|Hose}}.\n'
                 '[[dat|An]] {{dat|f|d[er]|Kasse}} [[dat|dankt]] er {{dat|f|d[er] freundlich[en]|Verkäuferin}}.\n'
                 'Draußen ist es kalt; deshalb [[akk|zieht]] er sofort {{akk|m|d[en] neu[en]|Mantel}} an.'],
  'b1': ['Qualität', 'Auswahl', 'umtauschen', 'jedenfalls', 'passend', 'vergleichen'],
  'recall': [('Was verlangt „mit“?', 'Dativ.'),
             ('Akkusativ von „die neue Jacke“?', 'die neue Jacke – feminin bleibt im Akkusativ gleich.'),
             ('Dativ von „die Bankkarte“?', 'der Bankkarte.'),
             ('Welche Endung hat ein maskulines Adjektiv nach „einen“?', '-en, z. B. einen dunklen Pullover.'),
             ('Welches Nomen ist neutrum: Kaufhaus oder Verkäufer?', 'das Kaufhaus.')]},
 {'number': 5,
  'title': 'Ein gemeinsames Abendessen',
  'targets': [('n', 'Frühstück', 'breakfast'),
              ('n', 'Mittagessen', 'lunch'),
              ('n', 'Abendessen', 'dinner'),
              ('n', 'Brot', 'bread'),
              ('n', 'Brötchen', 'bread roll'),
              ('f', 'Butter', 'butter'),
              ('m', 'Käse', 'cheese'),
              ('n', 'Ei', 'egg'),
              ('f', 'Milch', 'milk'),
              ('m', 'Kaffee', 'coffee'),
              ('m', 'Tee', 'tea'),
              ('n', 'Wasser', 'water'),
              ('m', 'Saft', 'juice'),
              ('n', 'Obst', 'fruit'),
              ('n', 'Gemüse', 'vegetables'),
              ('m', 'Apfel', 'apple'),
              ('f', 'Banane', 'banana'),
              ('f', 'Kartoffel', 'potato'),
              ('f', 'Tomate', 'tomato'),
              ('f', 'Suppe', 'soup'),
              ('m', 'Salat', 'salad'),
              ('n', 'Fleisch', 'meat'),
              ('m', 'Fisch', 'fish'),
              ('m', 'Reis', 'rice'),
              ('f', 'Nudel', 'noodle')],
  'paragraphs': ['[[dat|Am]] {{dat|m||Samstag}} [[akk|lädt]] Samir {{akk|m|zwei|Freunde}} ein. [[dat|Am]] '
                 '{{dat|m||Morgen}} gibt es {{akk|n|ein klein[es]|Frühstück}} [[dat|mit]] '
                 '{{dat|n||Brot}}, {{dat|n||Brötchen}}, {{dat|f||Butter}}, {{dat|m||Käse}}, {{dat|n||Ei}}, {{dat|f||Milch}}, {{dat|m||Kaffee}} und '
                 '{{dat|m||Tee}}. Später [[akk|plant]] er {{akk|n|d[as]|Abendessen}}. {{nom|m|D[er] frisch[e]|Salat}} steht schon [[dat|auf]] {{dat|m|d[em]|Tisch}}.',
                 'Samir [[akk|schneidet]] {{akk|f|d[ie] rot[e]|Tomate}} [[dat|mit]] {{dat|n|ein[em] '
                 'scharf[en]|Messer}}. Danach [[akk|kocht]] er {{akk|f||Kartoffeln}} und {{akk|m||Reis}}. {{nom|f|Ein[e]|Freundin}} bringt {{akk|n||Gemüse}}, '
                 '{{akk|n||Obst}}, {{akk|m||Äpfel}} und {{akk|f||Bananen}} mit. [[akk|Für]] {{akk|m|ein[en]|Gast}} gibt es {{akk|m||Fisch}}, [[akk|für]] den anderen etwas '
                 '{{akk|n||Fleisch}}. {{nom|f|D[ie]|Suppe}} bleibt warm [[dat|auf]] {{dat|m|d[em]|Herd}}.',
                 '[[dat|Beim]] {{dat|n||Essen}} [[akk|trinkt]] Samir {{akk|n|kalt[es]|Wasser}} [[dat|aus]] {{dat|n|ein[em] '
                 'groß[en]|Glas}}. Die anderen [[akk|trinken]] {{akk|m||Saft}}. [[dat|Zum]] {{dat|m||Nachtisch}} gibt es '
                 '{{akk|f|ein[e] süß[e]|Banane}} und '
                 'später noch {{akk|m||Kaffee}}. ((Nachdem|after)) alle satt sind, [[akk|räumen]] sie gemeinsam {{akk|f|d[ie]|Küche}} auf. '
                 '{{nom|f|Einige|Nudeln}} bleiben [[akk|für]] {{akk|n|d[as]|Mittagessen}} [[dat|am]] {{dat|m|nächst[en]|Tag}}.',
                 '[[dat|Beim]] {{dat|n|nächst[en]|Treffen}} kocht Lena.\n'
                 '{{nom|f|D[ie] gemeinsam[e]|Mahlzeit}} ist einfach, aber frisch.\n'
                 'Sie sprechen kurz [[akk|über]] {{akk|f||Ernährung}}, und Lena bereitet auch {{akk|n|ein '
                 'vegetarisch[es]|Gericht}} vor.\n'
                 'Samir hilft [[dat|beim]] {{dat|n||Vorbereiten}}: Er wäscht {{akk|n||Gemüse}}, [[akk|schneidet]] '
                 '{{akk|f||Zwiebeln}} und '
                 'stellt Gläser [[akk|auf]] {{akk|m|d[en]|Tisch}}.\n'
                 '{{nom|m|Ein|Apfel}} liegt noch [[dat|auf]] {{dat|m|d[em]|Tisch}}, und {{nom|f|ein[e]|Kartoffel}} rollt fast [[akk|auf]] '
                 '{{akk|m|d[en]|Boden}}. Zu {{dat|f|d[en]|Nudeln}} gibt es noch etwas Soße.\n'
                 'Danach können alle [[akk|genießen]] {{akk|n|d[as]|Essen}}. Es ist ausreichend [[akk|für]] '
                 '{{akk|f|vier|Personen}}.\n'
                 'Samir gibt {{akk|m|d[en] frisch[en]|Salat}} an Lena weiter und [[akk|nimmt]] selbst etwas {{akk|m||Reis}}.\n'
                 'Später räumen alle auf, [[akk|trocknen]] {{akk|n|d[as]|Geschirr}} und [[akk|stellen]] {{akk|n|d[ie]|Lebensmittel}} [[akk|in]] '
                 '{{akk|m|d[en]|Kühlschrank}}.'],
  'b1': ['Mahlzeit', 'Ernährung', 'vegetarisch', 'vorbereiten', 'genießen', 'ausreichend'],
  'recall': [('Dativ nach „aus“?', 'aus einem großen Glas.'),
             ('Akkusativ: ___ rote Tomate', 'die rote Tomate.'),
             ('Warum steht „Wasser“ im Akkusativ ohne Artikel?',
              'Stoffnamen können ohne Artikel stehen; die Satzfunktion ist trotzdem Akkusativ.'),
             ('Was ist der Artikel von „Salat“?', 'der Salat.'),
             ('Dativ von „das scharfe Messer“?', 'dem scharfen Messer.')]},
 {'number': 6,
  'title': 'Eine Reise nach Köln',
  'targets': [('f', 'Reise', 'trip/journey'),
              ('m', 'Urlaub', 'vacation'),
              ('n', 'Ticket', 'ticket'),
              ('f', 'Fahrkarte', 'travel ticket'),
              ('m', 'Zug', 'train'),
              ('f', 'Bahn', 'rail/train system'),
              ('n', 'Gleis', 'platform/track'),
              ('m', 'Flughafen', 'airport'),
              ('m', 'Flug', 'flight'),
              ('m', 'Pass', 'passport'),
              ('n', 'Hotel', 'hotel'),
              ('f', 'Rezeption', 'reception'),
              ('f', 'Reservierung', 'reservation'),
              ('m', 'Gast', 'guest'),
              ('m', 'Tourist', 'male tourist'),
              ('f', 'Touristin', 'female tourist'),
              ('m', 'Stadtplan', 'city map'),
              ('m', 'Reiseplan', 'travel plan'),
              ('f', 'Abfahrt', 'departure'),
              ('f', 'Ankunft', 'arrival'),
              ('f', 'Verspätung', 'delay'),
              ('f', 'Verbindung', 'connection'),
              ('m', 'Sitzplatz', 'seat'),
              ('m', 'Ausgang', 'exit'),
              ('m', 'Eingang', 'entrance')],
  'paragraphs': ['Ein paar Wochen später [[akk|macht]] Samir {{akk|f|ein[e]|Reise}}. {{nom|f|D[ie] geplant[e]|Abfahrt}} ist [[akk|um]] '
                 '{{akk|f|acht|Uhr}}. Er [[akk|kauft]] {{akk|n|ein günstig[es]|Ticket}} [[dat|an]] {{dat|m|d[em] '
                 'automatisch[en]|Schalter}} und geht [[dat|zum]] {{dat|n||Gleis}}. [[dat|Auf]] {{dat|f|d[er]|Fahrkarte}} stehen '
                 '{{nom|m||Zug}}, {{nom|f||Bahnverbindung}} und {{nom|m||Sitzplatz}}. Samir fährt gern [[dat|mit]] {{dat|f|d[er]|Bahn}}.',
                 'Wegen einer <<f|Verspätung>> muss er warten. {{nom|f|Ein[e]|Touristin}} fragt [[dat|nach]] '
                 '{{dat|m|d[em]|Ausgang}}, {{nom|m|ein|Tourist}} [[akk|sucht]] {{akk|m|d[en]|Eingang}}. Samir hilft [[dat|mit]] '
                 '{{dat|m|sein[em]|Stadtplan}}. Später [[akk|zeigt]] er {{akk|m|d[en] deutsch[en]|Pass}} [[dat|bei]] {{dat|f|d[er] '
                 'kurz[en]|Kontrolle}}. [[dat|Am]] {{dat|m||Flughafen}} [[dat|neben]] {{dat|m|d[em]|Bahnhof}} startet gerade {{nom|m|ein|Flug}}.',
                 '{{nom|f|D[ie] pünktlich[e]|Ankunft}} in Köln freut Samir. '
                 'In Köln geht Samir [[dat|zu]] {{dat|n|ein[em]|Hotel}}. [[dat|An]] {{dat|f|d[er]|Rezeption}} [[akk|findet]] '
                 '{{nom|f|d[ie]|Mitarbeiterin}} {{akk|f|sein[e]|Reservierung}}. {{nom|m|D[er] freundlich[e]|Gast}} vor ihm fragt [[dat|nach]] '
                 '{{dat|m|sein[em]|Reiseplan}}. ((Sobald|as soon as)) Samir {{akk|n|sein|Zimmer}} hat, [[akk|legt]] er {{akk|f|d[ie]|Fahrkarte}} weg und '
                 '[[akk|beginnt]] {{akk|m|sein[en] kurz[en]|Urlaub}}.',
                 '[[dat|Auf]] {{dat|f|d[er]|Rückreise}} ist {{nom|f|d[ie]|Verbindung}} nicht so einfach wie geplant. '
                 '{{nom|f|D[ie]|Bahn}} hat heute leider Verspätung.\n'
                 'Wegen einer Verspätung muss Samir in Bonn umsteigen. Er [[akk|findet]] trotzdem {{akk|f|ein[e] '
                 'günstig[e]|Unterkunft}} [[akk|für]] {{akk|f|ein[e]|Nacht}}.\n'
                 '[[dat|Am]] {{dat|m||Abend}} [[akk|besucht]] er noch {{akk|f|ein[e] bekannt[e]|Sehenswürdigkeit}}.\n'
                 'Wahrscheinlich hätte er sie [[akk|ohne]] {{akk|f|d[ie]|Verspätung}} nie gesehen.\n'
                 '[[dat|Am]] {{dat|m|nächst[en]|Morgen}} [[akk|nimmt]] er {{akk|m|d[en] früh[en]|Zug}} und erreicht '
                 'Frankfurt rechtzeitig. [[dat|Nach]] {{dat|f|d[er]|Ankunft}} ruft er sofort Lena an.\n'
                 'Er [[akk|packt]] {{akk|m|sein[en]|Koffer}} aus und [[akk|legt]] {{akk|f||Fahrkarte}}, {{akk|m||Pass}} '
                 'und {{akk|m||Stadtplan}} [[akk|in]] '
                 '{{akk|f|d[ie]|Schublade}}.'],
  'b1': ['Verbindung', 'Verspätung', 'umsteigen', 'Unterkunft', 'Sehenswürdigkeit', 'wahrscheinlich'],
  'recall': [('Was triggert „bei der kurzen Kontrolle“?', '„bei“ → Dativ.'),
             ('Akkusativ von „der deutsche Pass“?', 'den deutschen Pass.'),
             ('Dativ von „der automatische Schalter“?', 'dem automatischen Schalter.'),
             ('Warum ist „Ticket“ grün?', 'das Ticket → neutrum.'),
             ('Nominativ von „der freundliche Gast“?', 'der freundliche Gast.')]},
 {'number': 7,
  'title': 'Ein Besuch beim Arzt',
  'targets': [('m', 'Arzt', 'male doctor'),
              ('f', 'Ärztin', 'female doctor'),
              ('f', 'Praxis', "doctor's office/practice"),
              ('n', 'Krankenhaus', 'hospital'),
              ('m', 'Patient', 'male patient'),
              ('f', 'Patientin', 'female patient'),
              ('f', 'Krankheit', 'illness'),
              ('f', 'Gesundheit', 'health'),
              ('m', 'Schmerz', 'pain'),
              ('m', 'Kopf', 'head'),
              ('m', 'Hals', 'throat/neck'),
              ('m', 'Bauch', 'stomach/belly'),
              ('m', 'Rücken', 'back'),
              ('f', 'Hand', 'hand'),
              ('m', 'Fuß', 'foot'),
              ('n', 'Auge', 'eye'),
              ('n', 'Ohr', 'ear'),
              ('m', 'Zahn', 'tooth'),
              ('n', 'Medikament', 'medicine'),
              ('f', 'Tablette', 'tablet/pill'),
              ('n', 'Rezept', 'prescription/recipe'),
              ('m', 'Apotheker', 'male pharmacist'),
              ('f', 'Apothekerin', 'female pharmacist'),
              ('f', 'Untersuchung', 'examination'),
              ('f', 'Versicherung', 'insurance')],
  'paragraphs': ['[[dat|Nach]] {{dat|f|d[er]|Reise}} fühlt sich Samir nicht gut. {{nom|m|D[er] stark[e]|Schmerz}} beginnt [[dat|im]] '
                 '{{dat|m||Rücken}} und später auch [[dat|im]] {{dat|m||Hals}}. Er [[akk|ruft]] {{akk|f|ein[e]|Praxis}} an und '
                 '[[akk|bekommt]] schnell {{akk|m|ein[en]|Termin}}. [[dat|Im]] {{dat|n||Wartezimmer}} sitzt schon {{nom|m|ein|Patient}} und wartet '
                 '[[akk|auf]] {{akk|m|d[en]|Arzt}} der Nachbarpraxis. {{nom|m|D[er]|Arzt}} nickt Samir freundlich zu. '
                 '{{nom|f|D[ie] ruhig[e]|Ärztin}} begrüßt ihn.',
                 'Sie [[akk|untersucht]] {{akk|m|d[en] verspannt[en]|Rücken}} und [[akk|schaut]] auch [[akk|auf]] {{akk|m||Kopf}}, '
                 '{{akk|m||Bauch}}, {{akk|f||Hand}}, {{akk|m||Fuß}}, {{akk|n||Auge}}, {{akk|n||Ohr}} und {{akk|m||Zahn}}. Danach spricht sie mit '
                 'Samir [[akk|über]] {{akk|f||Gesundheit}} und {{akk|f|möglich[e]|Ursachen}}. [[dat|Im]] {{dat|n||Krankenhaus}} wäre {{nom|f|ein[e] größer[e]|Untersuchung}} möglich, aber das ist nicht nötig.',
                 '{{nom|f|D[ie]|Ärztin}} [[akk|gibt]] ihm {{akk|n|ein|Rezept}}. Samir [[akk|holt]] {{akk|n|d[as] passend[e]|Medikament}} '
                 '[[dat|bei]] {{dat|f|d[er] nah[en]|Apothekerin}}. {{nom|m|Ein|Apotheker}} [[dat|erklärt]] {{dat|f|ein[er]|Patientin}}, '
                 'wie sie {{akk|f|ihr[e]|Tablette}} [[akk|nehmen]] soll. Später hilft {{nom|f|d[ie]|Ärztin}} auch '
                 '{{dat|m|d[em]|Patienten}} von nebenan. ((Falls|in case/if)) {{nom|f|d[ie]|Krankheit}} länger dauert, '
                 'soll Samir noch einmal kommen. {{nom|f|Sein[e]|Versicherung}} [[akk|übernimmt]] {{akk|f|d[ie] normal[e]|Untersuchung}}.',
                 '[[dat|Nach]] {{dat|m|drei|Tagen}} sind Samirs Beschwerden schwächer.\n'
                 '{{nom|f|D[ie]|Ärztin}} erklärt, dass {{nom|f|d[ie]|Behandlung}} Zeit braucht.\n'
                 '{{nom|f|Ein[e] möglich[e]|Ursache}} ist zu langes Sitzen [[dat|im]] {{dat|n||Büro}}. Samir soll '
                 '{{akk|f|schwer[e]|Arbeit}} vermeiden.\n'
                 '{{nom|f|D[ie]|Ärztin}} kann ihm außerdem {{akk|f|leicht[e]|Bewegung}} empfehlen; er soll sie '
                 'regelmäßig machen.\n'
                 'Zu Hause [[dat|folgt]] Samir {{dat|m|d[em] gut[en]|Rat}} und ruht sich aus.\n'
                 'Er [[akk|trinkt]] viel {{akk|n||Wasser}}, schläft früh und [[akk|nimmt]] {{akk|n|d[as]|Medikament}} genau [[dat|nach]] '
                 '{{dat|n|d[em]|Rezept}}.\n'
                 'Bald kann er wieder [[akk|ohne]] {{akk|m||Schmerzen}} spazieren gehen.'],
  'b1': ['Beschwerden', 'Behandlung', 'Ursache', 'vermeiden', 'empfehlen', 'regelmäßig'],
  'recall': [('Akkusativ: ___ verspannten Rücken', 'den verspannten Rücken.'),
             ('Dativ nach „bei“?', 'bei der nahen Apothekerin.'),
             ('Was ist der Artikel von „Medikament“?', 'das Medikament.'),
             ('Welche Form hat „die Ärztin“ im Nominativ?', 'die ruhige Ärztin.'),
             ('Dativ von „der Patient“?', 'dem Patienten (n-Deklination).')]},
 {'number': 8,
  'title': 'Ein Vormittag auf dem Amt',
  'targets': [('n', 'Amt', 'office/authority'),
              ('f', 'Behörde', 'authority'),
              ('n', 'Formular', 'form'),
              ('m', 'Antrag', 'application'),
              ('m', 'Ausweis', 'ID card'),
              ('f', 'Anmeldung', 'registration'),
              ('f', 'Bescheinigung', 'certificate'),
              ('f', 'Unterschrift', 'signature'),
              ('n', 'Datum', 'date'),
              ('n', 'Geburtsdatum', 'date of birth'),
              ('m', 'Name', 'name'),
              ('m', 'Vorname', 'first name'),
              ('m', 'Nachname', 'surname'),
              ('f', 'Nummer', 'number'),
              ('f', 'Kopie', 'copy'),
              ('n', 'Original', 'original'),
              ('f', 'Gebühr', 'fee'),
              ('m', 'Schalter', 'counter'),
              ('m', 'Mitarbeiter', 'male employee'),
              ('f', 'Mitarbeiterin', 'female employee'),
              ('f', 'Wartezeit', 'waiting time'),
              ('m', 'Brief', 'letter'),
              ('m', 'Umschlag', 'envelope'),
              ('m', 'Stempel', 'stamp'),
              ('m', 'Aufenthaltstitel', 'residence permit')],
  'paragraphs': ['[[akk|Für]] {{akk|f|d[ie]|Anmeldung}} geht Samir [[akk|auf]] {{akk|n|ein|Amt}}. {{nom|n|D[as] zuständig[e]|Amt}} liegt '
                 '[[dat|in]] {{dat|n|ein[em] groß[en]|Gebäude}}. [[dat|Am]] {{dat|m||Eingang}} [[akk|nimmt]] er {{akk|f|ein[e]|Nummer}}. Vor ihm wartet '
                 '{{nom|f|ein[e]|Mitarbeiterin}}, [[dat|hinter]] {{dat|m|ein[em]|Schalter}} sitzt {{nom|m|ein|Mitarbeiter}}.',
                 'Samir [[akk|füllt]] {{akk|n|d[as] lang[e]|Formular}} [[dat|mit]] {{dat|m|ein[em] blau[en]|Stift}} '
                 'aus. Er [[akk|schreibt]] {{akk|m||Name}}, {{akk|m||Vorname}}, {{akk|m||Nachname}}, {{akk|n||Geburtsdatum}} und {{akk|n||Datum}} '
                 'hinein. Danach [[akk|legt]] er {{akk|m||Ausweis}}, {{akk|f||Kopie}} und {{akk|n||Original}} [[akk|auf]] {{akk|m|d[en]|Tisch}}. [[akk|Für]] '
                 '{{akk|m|d[en]|Antrag}} [[akk|braucht]] er außerdem {{akk|f|ein[e]|Unterschrift}}.',
                 '{{nom|m|D[er]|Mitarbeiter}} [[akk|prüft]] {{akk|f|d[ie]|Anmeldung}} und [[akk|gibt]] Samir {{akk|f|ein[e]|Bescheinigung}}. [[akk|Für]] '
                 '{{akk|m|d[en]|Aufenthaltstitel}} ist später {{nom|f|ein[e] ander[e]|Behörde}} zuständig. Samir '
                 '[[akk|steckt]] {{akk|m|d[en] wichtig[en]|Brief}} [[akk|in]] {{akk|m|ein[en] weiß[en]|Umschlag}}. '
                 '((Bevor|before)) er geht, [[akk|bezahlt]] er {{akk|f|ein[e] klein[e]|Gebühr}} und bekommt {{akk|m|ein[en]|Stempel}}. '
                 '{{nom|f|D[ie]|Wartezeit}} war kürzer als erwartet.',
                 '{{akk|f|Einig[e]|Wochen}} später [[akk|braucht]] Samir noch {{akk|n|ein|Dokument}}.\n'
                 'Diesmal weiß er schon, {{nom|f|welch[e]|Stelle}} zuständig ist und {{akk|f|welch[e]|Unterlagen}} er '
                 'mitbringen muss.\n'
                 '[[akk|Für]] {{akk|n|ein weiter[es]|Dokument}} [[akk|braucht]] er noch {{akk|f|ein[e]|Bescheinigung}} [[dat|von]] {{dat|f|d[er]|Polizei}}.\n'
                 '{{nom|m|Sein|Chef}} [[akk|unterschreibt]] dafür {{akk|n|ein zusätzlich[es]|Formular}}.\n'
                 'Er möchte {{akk|f|ein[e]|Bescheinigung}} [[akk|beantragen]].\n'
                 '{{nom|f|D[ie]|Mitarbeiterin}} [[akk|prüft]] {{akk|m|d[ie]|Daten}} und bestätigt, dass alles '
                 'vollständig ist.\n'
                 'Nur {{nom|f|ein[e] zusätzlich[e]|Kopie}} ist erforderlich. Zum Glück endet {{nom|f|d[ie]|Frist}} '
                 'erst {{akk|f|nächst[e]|Woche}}.\n'
                 'Samir [[akk|legt]] {{akk|m|d[en] gültig[en]|Ausweis}} [[akk|auf]] {{akk|m|d[en]|Schalter}},\n'
                 '[[akk|unterschreibt]] {{akk|n|d[as]|Formular}} und [[akk|bezahlt]] {{akk|f|d[ie]|Gebühr}}.\n'
                 '[[dat|Nach]] {{dat|f|kurz[er]|Wartezeit}} kann er alles mitnehmen.'],
  'b1': ['zuständig', 'Unterlagen', 'beantragen', 'bestätigen', 'erforderlich', 'Frist'],
  'recall': [('Was verlangt „mit“?', 'Dativ: mit einem blauen Stift.'),
             ('Akkusativ von „das lange Formular“?', 'das lange Formular.'),
             ('Warum heißt es „einen weißen Umschlag“?', 'Maskulin Akkusativ → einen; Adjektiv -en.'),
             ('Artikel von „Gebühr“?', 'die Gebühr.'),
             ('Dativ von „das zuständige Amt“?', 'dem zuständigen Amt.')]},
 {'number': 9,
  'title': 'Im Deutschkurs',
  'targets': [('m', 'Kurs', 'course'),
              ('f', 'Sprache', 'language'),
              ('n', 'Deutsch', 'German'),
              ('n', 'Wort', 'word'),
              ('m', 'Satz', 'sentence'),
              ('f', 'Frage', 'question'),
              ('f', 'Antwort', 'answer'),
              ('f', 'Übung', 'exercise'),
              ('f', 'Hausaufgabe', 'homework'),
              ('n', 'Buch', 'book'),
              ('n', 'Heft', 'notebook'),
              ('f', 'Seite', 'page'),
              ('n', 'Kapitel', 'chapter'),
              ('n', 'Beispiel', 'example'),
              ('m', 'Fehler', 'mistake'),
              ('f', 'Grammatik', 'grammar'),
              ('f', 'Aussprache', 'pronunciation'),
              ('m', 'Lehrer', 'male teacher'),
              ('f', 'Lehrerin', 'female teacher'),
              ('m', 'Schüler', 'male student/pupil'),
              ('f', 'Schülerin', 'female student/pupil'),
              ('f', 'Prüfung', 'exam'),
              ('m', 'Test', 'test'),
              ('f', 'Note', 'grade'),
              ('n', 'Zertifikat', 'certificate')],
  'paragraphs': ['Samir besucht jetzt zweimal pro Woche {{akk|m|ein[en]|Kurs}}. {{nom|f|D[ie] geduldig[e]|Lehrerin}} '
                 'beginnt [[dat|mit]] {{dat|f|ein[er] kurz[en]|Übung}}. [[dat|Auf]] {{dat|f|jed[er]|Seite}} [[dat|im]] '
                 '{{dat|n||Buch}} steht {{nom|n|ein|Beispiel}}, und [[dat|im]] {{dat|n||Heft}} schreibt Samir '
                 '{{akk|n|neu[e]|Wörter}} und {{akk|m||Sätze}}.',
                 '{{nom|f|D[ie]|Lehrerin}} [[akk|erklärt]] {{akk|f|d[ie] schwierig[e]|Grammatik}} [[dat|mit]] '
                 '{{dat|n|ein[em] einfach[en]|Beispiel}}. Danach [[akk|stellt]] sie {{akk|f|ein[e]|Frage}}, und {{nom|m|ein|Schüler}} '
                 '[[akk|gibt]] {{akk|f|ein[e]|Antwort}}. {{nom|f|Ein[e]|Schülerin}} [[akk|übt]] {{akk|f|d[ie]|Aussprache}}. Samir macht '
                 '{{akk|m|ein[en]|Fehler}}, aber er verbessert ihn selbst. {{nom|n|Ein neu[es]|Wort}} merkt er sich '
                 'sofort; [[dat|in]] {{dat|m|ein[em] lang[en]|Satz}} hilft ihm oft {{nom|m|d[er]|Kontext}}.',
                 '[[akk|Für]] {{akk|f|d[ie]|Hausaufgabe}} [[akk|liest]] {{nom|f|d[ie]|Gruppe}} {{akk|n|ein|Kapitel}}. [[dat|Vor]] '
                 '{{dat|f|d[er]|Prüfung}} gibt es noch '
                 '{{akk|m|ein[en]|Test}}; später [[akk|bekommt]] jeder {{akk|f|ein[e]|Note}} und [[dat|am]] {{dat|n||Ende}} '
                 '{{akk|n|ein|Zertifikat}}. ((Je '
                 'öfter|the more often)) Samir [[akk|hört]] {{akk|n||Deutsch}}, desto natürlicher werden {{nom|f|einig[e]|Formen}}. Manchmal '
                 '[[akk|unterrichtet]] auch {{nom|m|ein erfahren[er]|Lehrer}} {{akk|f|d[ie]|Gruppe}}. Er merkt '
                 'besonders, dass {{nom|m||Artikel}} und {{nom|n||Adjektive}} langsam automatisch kommen.',
                 '{{nom|f|D[ie] deutsch[e]|Sprache}} wird für Samir langsam vertrauter, weil er {{akk|f|d[ie]|Sprache}} '
                 '{{akk|m|jed[en]|Abend}} übt. '
                 '[[dat|Im]] {{dat|m||Kurs}} sieht Samir langsam {{akk|m|sein[en]|Fortschritt}}.\n'
                 '{{akk|n|Neu[e]|Wörter}} [[akk|versteht]] er oft [[dat|aus]] {{dat|m|d[em]|Kontext}}, und [[dat|bei]] '
                 '{{dat|m|schwierig[en]|Sätzen}} '
                 'fragt er [[dat|nach]] {{dat|f|d[er]|Bedeutung}}.\n'
                 '{{nom|f|D[ie]|Lehrerin}} [[akk|fordert]] {{akk|f|d[ie]|Gruppe}} auf, {{akk|m|eigen[e]|Gedanken}} auszudrücken.\n'
                 'Ein Übungssatz handelt [[akk|über]] {{akk|m|ein[en]|Chef}}, der seinem Team dankt; ein anderer davon, dass '
                 '{{nom|f|d[ie]|Polizei}} schnell hilft, wenn es nötig ist.\n'
                 'Am Ende [[dat|dankt]] {{nom|f|d[ie]|Gruppe}} {{dat|m|d[em]|Lehrer}} [[akk|für]] {{akk|m|d[en]|Kurs}}.\n'
                 'Samir arbeitet dabei immer selbstständiger. Zu Hause muss er {{akk|f|wichtig[e]|Formen}} wiederholen, damit sich '
                 '{{nom|f|sein[e]|Aussprache}} weiter verbessert.\n'
                 '[[dat|Im]] {{dat|m||Unterricht}} [[akk|beschreibt]] er {{akk|n|d[as] neu[e]|Bild}} [[dat|mit]] '
                 '{{dat|m|einfach[en]|Sätzen}}.\n'
                 'Danach [[akk|vergleicht]] {{nom|f|d[ie]|Gruppe}} {{akk|f|ihr[e]|Antworten}}. {{nom|m||Fehler}} sind erlaubt; wichtig ist, '
                 'dass jeder spricht.'],
  'b1': ['Fortschritt', 'Bedeutung', 'ausdrücken', 'selbstständig', 'wiederholen', 'verbessern'],
  'recall': [('Dativ nach „mit“?', 'mit einem einfachen Beispiel.'),
             ('Akkusativ von „die schwierige Grammatik“?', 'die schwierige Grammatik.'),
             ('Was ist der Artikel von „Beispiel“?', 'das Beispiel.'),
             ('Plural-Hinweis: „Wörter“ gehört zu welchem Singular?', 'das Wort.'),
             ('Welche Form: mit ___ geduldigen Lehrerin?', 'mit der geduldigen Lehrerin.')]},
 {'number': 10,
  'title': 'Sport und Freizeit',
  'targets': [('f', 'Freizeit', 'free time'),
              ('n', 'Hobby', 'hobby'),
              ('m', 'Sport', 'sport'),
              ('m', 'Fußball', 'football/soccer'),
              ('n', 'Tennis', 'tennis'),
              ('n', 'Schwimmen', 'swimming'),
              ('n', 'Fitnessstudio', 'gym'),
              ('m', 'Verein', 'club'),
              ('f', 'Mannschaft', 'team'),
              ('m', 'Spieler', 'male player'),
              ('f', 'Spielerin', 'female player'),
              ('m', 'Ball', 'ball'),
              ('n', 'Spiel', 'game'),
              ('n', 'Training', 'training'),
              ('m', 'Trainer', 'male coach'),
              ('f', 'Trainerin', 'female coach'),
              ('m', 'Platz', 'place/field'),
              ('f', 'Halle', 'hall'),
              ('n', 'Schwimmbad', 'swimming pool'),
              ('m', 'Eintritt', 'admission'),
              ('f', 'Bewegung', 'movement/exercise'),
              ('m', 'Spaziergang', 'walk'),
              ('f', 'Musik', 'music'),
              ('m', 'Film', 'film'),
              ('n', 'Kino', 'cinema')],
  'paragraphs': ['[[dat|Nach]] {{dat|m|d[em]|Kurs}} möchte Samir {{akk|f|mehr|Bewegung}}. {{nom|m|D[er] neu[e]|Verein}} '
                 '[[akk|bietet]] {{akk|m||Fußball}}, '
                 '{{akk|n||Tennis}} und {{akk|n||Schwimmen}} an. {{nom|m|Ein|Freund}} [[akk|empfiehlt]] außerdem {{akk|n|ein|Fitnessstudio}}. Samir '
                 'entscheidet sich zuerst [[akk|für]] {{akk|m||Fußball}}.',
                 '[[dat|Beim]] {{dat|n||Training}} [[akk|passt]] er {{akk|m|d[en] rund[en]|Ball}} [[dat|zu]] {{dat|f|d[er] '
                 'schnell[en]|Spielerin}}. {{nom|m|D[er]|Trainer}} [[akk|erklärt]] {{akk|n|d[as]|Spiel}}, {{nom|f|D[ie]|Trainerin}} [[akk|beobachtet]] '
                 '{{akk|f|d[ie]|Mannschaft}}. Später üben {{nom|m||Spieler}} und {{nom|f||Spielerinnen}} gemeinsam [[dat|in]] {{dat|f|d[er]|Halle}} und '
                 '[[dat|auf]] {{dat|m|d[em]|Platz}}.',
                 '[[dat|Am]] {{dat|n||Wochenende}} geht Samir [[akk|ins]] {{akk|n||Schwimmbad}}. {{nom|m|D[er]|Eintritt}} kostet nur '
                 'wenig; er [[akk|bezahlt]] {{akk|m|d[en]|Eintritt}} direkt [[dat|an]] {{dat|f|d[er]|Kasse}}. '
                 'Nach {{dat|m|d[em]|Sport}} macht er '
                 '{{akk|m|ein[en]|Spaziergang}}. [[dat|Am]] {{dat|m||Abend}} [[akk|hört]] er {{akk|f||Musik}} oder sieht {{akk|m|ein[en]|Film}} '
                 '[[dat|im]] {{dat|n||Kino}}. ((Außerdem|in addition)) [[akk|entdeckt]] er {{akk|n|ein neu[es]|Hobby}}: Er '
                 '[[akk|fotografiert]] {{akk|f|klein[e]|Szenen}} [[dat|aus]] {{dat|f|sein[er]|Freizeit}}.',
                 '[[dat|Beim]] {{dat|m||Fußball}} merkt Samir, dass {{nom|f||Technik}} nicht alles ist.\n'
                 '[[akk|Für]] {{akk|n|länger[e]|Spiele}} braucht er mehr {{akk|f||Ausdauer}}.\n'
                 '{{nom|m|D[er]|Verein}} [[akk|organisiert]] {{akk|m|ein[en] klein[en]|Wettbewerb}}, und '
                 '{{nom|f|d[ie]|Mannschaft}} ist sehr motiviert.\n'
                 '{{nom|m|D[er]|Trainer}} spricht [[akk|über]] {{akk|f|persönlich[e]|Leistung}} und darüber, wie man sich [[akk|an]] '
                 '{{akk|n|regelmäßig[es]|Training}} gewöhnt.\n'
                 'Samir lernt auch, [[dat|bei]] {{dat|n|ein[em] lang[en]|Spiel}} durchzuhalten.\n'
                 'Er spielt [[dat|mit]] {{dat|f|d[er] schnell[en]|Spielerin}} [[dat|auf]] {{dat|f|d[er] '
                 'recht[en]|Seite}} und passt {{akk|m|d[en]|Ball}} häufiger.\n'
                 '[[dat|Nach]] {{dat|n|d[em]|Training}} schwimmen {{nom|m|einig[e]|Freunde}} noch {{akk|f|ein[e] halb[e]|Stunde}}.'],
  'b1': ['Ausdauer', 'Wettbewerb', 'motiviert', 'Leistung', 'sich gewöhnen', 'durchhalten'],
  'recall': [('Was triggert „zu der schnellen Spielerin“?', '„zu“ → Dativ.'),
             ('Akkusativ von „der runde Ball“?', 'den runden Ball.'),
             ('Dativ von „der neue Verein“?', 'dem neuen Verein.'),
             ('Artikel von „Training“?', 'das Training.'),
             ('Warum ist „Mannschaft“ feminin?',
              'Es heißt die Mannschaft; -schaft ist zudem ein sehr zuverlässiges feminines Suffix.')]},
 {'number': 11,
  'title': 'Abend im Restaurant',
  'targets': [('n', 'Restaurant', 'restaurant'),
              ('n', 'Café', 'café'),
              ('m', 'Kellner', 'waiter'),
              ('f', 'Kellnerin', 'waitress'),
              ('f', 'Speisekarte', 'menu'),
              ('n', 'Getränk', 'drink'),
              ('n', 'Gericht', 'dish'),
              ('f', 'Vorspeise', 'starter'),
              ('n', 'Hauptgericht', 'main course'),
              ('m', 'Nachtisch', 'dessert'),
              ('f', 'Bestellung', 'order'),
              ('n', 'Trinkgeld', 'tip'),
              ('f', 'Gabel', 'fork'),
              ('n', 'Messer', 'knife'),
              ('m', 'Löffel', 'spoon'),
              ('m', 'Teller', 'plate'),
              ('f', 'Tasse', 'cup'),
              ('n', 'Glas', 'glass'),
              ('f', 'Flasche', 'bottle'),
              ('n', 'Salz', 'salt'),
              ('m', 'Pfeffer', 'pepper'),
              ('m', 'Zucker', 'sugar'),
              ('m', 'Hunger', 'hunger'),
              ('m', 'Durst', 'thirst'),
              ('m', 'Geschmack', 'taste')],
  'paragraphs': ['[[dat|Nach]] {{dat|m|d[em]|Sport}} trifft Samir Lena in {{dat|n|ein[em]|Restaurant}}. {{nom|f|D[ie] '
                 'freundlich[e]|Kellnerin}} [[akk|bringt]] {{akk|f|d[ie]|Speisekarte}}. Beide [[akk|haben]] {{akk|m||Hunger}} und {{akk|m||Durst}}. '
                 '[[dat|Auf]] {{dat|f|d[er]|Karte}} stehen {{nom|f||Vorspeise}}, {{nom|n||Hauptgericht}}, {{nom|m||Nachtisch}} und {{nom|n|verschieden[e]|Getränke}}.',
                 'Samir [[akk|bestellt]] {{akk|n|ein warm[es]|Gericht}} [[dat|bei]] {{dat|m|d[em] jung[en]|Kellner}} '
                 'und dazu noch {{akk|n|ein|Getränk}}. '
                 'Lena [[akk|nimmt]] {{akk|f|ein[e]|Suppe}} als Vorspeise. [[dat|Auf]] {{dat|m|d[em]|Tisch}} liegen {{nom|f||Gabel}}, {{nom|n||Messer}} und '
                 '{{nom|m||Löffel}}; daneben stehen {{nom|m||Teller}}, {{nom|f||Tasse}}, {{nom|n||Glas}} und {{nom|f||Flasche}}. {{nom|n||Salz}}, '
                 '{{nom|m||Pfeffer}} und {{nom|m||Zucker}} stehen [[dat|in]] {{dat|f|d[er]|Mitte}}.',
                 '[[dat|Nach]] {{dat|n|d[em]|Essen}} sprechen sie [[akk|über]] {{akk|m|d[en]|Geschmack}}. Samir [[akk|bezahlt]] {{akk|f|d[ie] '
                 'gemeinsam[e]|Bestellung}} [[dat|mit]] {{dat|f|sein[er] neu[en]|Karte}} und [[akk|lässt]] {{akk|n||Trinkgeld}} da. '
                 '((Obwohl|although)) {{nom|n|D[as]|Café}} nebenan noch offen ist, gehen beide nach Hause.',
                 '{{akk|m|Ein|Monat}} später gehen Samir und Lena wieder essen.\n'
                 'Diesmal ist {{nom|f|d[ie]|Atmosphäre}} ruhiger, und {{nom|m|d[er]|Service}} ist besonders '
                 'aufmerksam.\n'
                 '[[dat|An]] {{dat|m|ein[em] ander[en]|Tisch}} [[akk|lobt]] {{nom|m|ein ander[er]|Kunde}} {{akk|n|d[as]|Essen}}: Diesmal [[akk|nimmt]] er lieber '
                 '{{akk|m|ein[en] frisch[en]|Apfel}} als Nachtisch. [[dat|Zu]] {{dat|f|d[en]|Kartoffeln}} gibt es '
                 'außerdem {{akk|f||Nudeln}} mit Soße.\n'
                 '[[dat|Am]] {{dat|m||Nachbartisch}} hat {{nom|m|ein|Gast}} {{akk|f|ein[e]|Beschwerde}} und möchte '
                 '{{akk|n|sein|Gericht}} [[akk|reklamieren]].\n'
                 '{{nom|m|D[er]|Kellner}} reagiert höflich und [[akk|nimmt]] {{akk|f||Rücksicht}} [[akk|auf]] {{akk|m|d[en]|Wunsch}} des '
                 'Gastes.\n'
                 '[[dat|Am]] {{dat|n||Ende}} sind alle zufrieden.\n'
                 'Samir [[akk|bestellt]] {{akk|n|ein lecker[es]|Hauptgericht}}, Lena nimmt nur '
                 '{{akk|f|ein[e]|Vorspeise}}.\n'
                 'Beide [[akk|probieren]] {{akk|m|d[en]|Nachtisch}} und [[akk|teilen]] sich {{akk|f|ein[e]|Flasche}} Wasser.'],
  'b1': ['Atmosphäre', 'Service', 'Beschwerde', 'reklamieren', 'Rücksicht', 'zufrieden'],
  'recall': [('Dativ: bei ___ jungen Kellner', 'bei dem jungen Kellner / beim jungen Kellner.'),
             ('Akkusativ von „ein warmes Gericht“?', 'ein warmes Gericht.'),
             ('Was triggert „mit seiner neuen Karte“?', 'mit → Dativ.'),
             ('Artikel von „Speisekarte“?', 'die Speisekarte.'),
             ('Dativ von „das Glas“?', 'dem Glas.')]},
 {'number': 12,
  'title': 'Familienbesuch',
  'targets': [('f', 'Familie', 'family'),
              ('f', 'Mutter', 'mother'),
              ('m', 'Vater', 'father'),
              ('m', 'Sohn', 'son'),
              ('f', 'Tochter', 'daughter'),
              ('m', 'Bruder', 'brother'),
              ('f', 'Schwester', 'sister'),
              ('m', 'Großvater', 'grandfather'),
              ('f', 'Großmutter', 'grandmother'),
              ('m', 'Onkel', 'uncle'),
              ('f', 'Tante', 'aunt'),
              ('m', 'Cousin', 'male cousin'),
              ('f', 'Cousine', 'female cousin'),
              ('n', 'Kind', 'child'),
              ('n', 'Baby', 'baby'),
              ('m', 'Ehemann', 'husband'),
              ('f', 'Ehefrau', 'wife'),
              ('f', 'Hochzeit', 'wedding'),
              ('m', 'Geburtstag', 'birthday'),
              ('n', 'Geschenk', 'gift'),
              ('m', 'Besuch', 'visit'),
              ('f', 'Einladung', 'invitation'),
              ('f', 'Feier', 'celebration'),
              ('n', 'Foto', 'photo'),
              ('f', 'Erinnerung', 'memory')],
  'paragraphs': ['[[dat|Im]] {{dat|m||Frühling}} [[akk|bekommt]] Samir {{akk|m||Besuch}} [[dat|von]] {{dat|f|sein[er]|Familie}}. '
                 '{{nom|f|D[ie] groß[e]|Familie}} '
                 'kommt [[dat|am]] {{dat|m||Freitag}}: {{nom|f||Mutter}}, {{nom|m||Vater}}, {{nom|m||Bruder}}, {{nom|f||Schwester}}, {{nom|m||Onkel}}, '
                 '{{nom|f||Tante}}, {{nom|m||Cousin}} und {{nom|f||Cousine}}. Später kommen auch {{nom|m||Großvater}} und '
                 '{{nom|f||Großmutter}}. {{nom|f|D[ie]|Bahn}} ist pünktlich, und Samir freut sich [[akk|auf]] '
                 '{{akk|f|d[ie]|Ankunft}} seiner Familie.',
                 'Samirs {{nom|f||Schwester}} [[akk|bringt]] {{akk|n|ihr|Baby}} mit. Ihr Bruder kommt [[dat|mit]] {{dat|f|sein[er]|Ehefrau}}, '
                 '{{dat|m|sein[em]|Sohn}} und {{dat|f|sein[er]|Tochter}}. {{nom|m|Ein|Cousin}} [[akk|zeigt]] {{akk|n||Fotos}} [[dat|von]] '
                 '{{dat|f|ein[er]|Hochzeit}}. Samir [[akk|gibt]] {{akk|n|ein klein[es]|Geschenk}} [[dat|an]] '
                 '{{dat|f|sein[e] jung[e]|Cousine}} weiter. {{nom|n|Ein|Kind}} spielt [[dat|im]] {{dat|n||Wohnzimmer}}, während '
                 '{{nom|m|d[er]|Ehemann}} seiner <<f|Tante>> [[dat|mit]] {{dat|m|d[em]|Vater}} spricht. {{nom|m|D[er]|Sohn}} '
                 'spielt fröhlich [[dat|mit]] {{dat|m|d[em]|Ball}}, {{nom|f|d[ie]|Tochter}} [[akk|malt]] {{akk|n|ein|Bild}}, und {{nom|f|d[ie]|Ehefrau}} '
                 'unterhält sich [[dat|mit]] Samirs {{dat|f||Mutter}}.',
                 '[[dat|Am]] {{dat|m||Samstag}} feiern sie {{akk|m|ein[en]|Geburtstag}}. Es [[akk|gibt]] {{akk|f|ein[e]|Einladung}}, {{akk|f|ein[e] klein[e]|Feier}} und {{akk|n|viel[e]|Fotos}}. '
                 '((Während|while)) des Besuchs [[akk|erzählen]] alle {{akk|f|alt[e]|Geschichten}} und '
                 '{{nom|f|neu[e]|Erinnerungen}} entstehen. Samir wird {{akk|f|dies[e]|Erinnerung}} lange behalten. '
                 '[[dat|Am]] {{dat|m||Sonntag}} [[akk|begleitet]] Samir {{akk|f|sein[e]|Familie}} zum {{dat|m||Bahnhof}} und winkt lange.',
                 '[[dat|Nach]] {{dat|m|d[em]|Familienbesuch}} denkt Samir [[akk|über]] {{akk|f|sein[e]|Beziehungen}} '
                 'nach.\n'
                 '[[dat|Mit]] manchen Verwandten hat er besonders {{akk|n|viel|Vertrauen}}.\n'
                 'Natürlich gibt es manchmal {{akk|m||Streit}}, aber meistens können sie sich schnell wieder '
                 'versöhnen.\n'
                 '{{nom|f|Sein[e]|Schwester}} versucht ihn [[dat|bei]] {{dat|f|wichtig[en]|Entscheidungen}} zu unterstützen.\n'
                 '[[dat|Nach]] {{dat|f|d[er]|Abreise}} beginnt Samir {{akk|f|d[ie]|Familie}} schon zu vermissen.\n'
                 'Er [[dat|schreibt]] {{dat|f|sein[er] älter[en]|Schwester}} {{akk|f|ein[e]|Nachricht}}\n'
                 'und [[dat|schickt]] {{dat|m|d[em]|Großvater}} {{akk|n|ein|Foto}} [[dat|von]] {{dat|f|d[er]|Feier}}.'],
  'b1': ['Beziehungen', 'Vertrauen', 'Streit', 'sich versöhnen', 'unterstützen', 'vermissen'],
  'recall': [('Akkusativ von „ein kleines Geschenk“?', 'ein kleines Geschenk.'),
             ('Dativ von „die junge Cousine“?', 'der jungen Cousine.'),
             ('Artikel von „Baby“?', 'das Baby.'),
             ('Welche Präposition steht mit Dativ: von oder für?', 'von.'),
             ('Warum ist „Familie“ feminin?', 'Es heißt die Familie.')]},
 {'number': 13,
  'title': 'Ein wechselhaftes Wochenende',
  'targets': [('n', 'Wetter', 'weather'),
              ('f', 'Sonne', 'sun'),
              ('m', 'Regen', 'rain'),
              ('m', 'Schnee', 'snow'),
              ('m', 'Wind', 'wind'),
              ('f', 'Wolke', 'cloud'),
              ('m', 'Himmel', 'sky'),
              ('f', 'Temperatur', 'temperature'),
              ('m', 'Grad', 'degree'),
              ('m', 'Frühling', 'spring'),
              ('m', 'Sommer', 'summer'),
              ('m', 'Herbst', 'autumn'),
              ('m', 'Winter', 'winter'),
              ('f', 'Jahreszeit', 'season'),
              ('m', 'Morgen', 'morning'),
              ('m', 'Mittag', 'midday/noon'),
              ('m', 'Abend', 'evening'),
              ('f', 'Nacht', 'night'),
              ('n', 'Wochenende', 'weekend'),
              ('f', 'Woche', 'week'),
              ('m', 'Monat', 'month'),
              ('n', 'Jahr', 'year'),
              ('m', 'Wetterbericht', 'weather forecast'),
              ('m', 'Schirm', 'umbrella'),
              ('m', 'Sturm', 'storm')],
  'paragraphs': ['{{nom|n|D[as]|Wetter}} ändert sich schnell. {{nom|m|D[er] grau[e]|Himmel}} zeigt morgens {{akk|f|viel[e]|Wolken}}, '
                 'später kommt {{nom|f|D[ie]|Sonne}}. {{nom|f|Ein[e] letzt[e]|Wolke}} bleibt noch lange [[dat|am]] {{dat|m||Himmel}}. '
                 '{{nom|m|D[er]|Wetterbericht}} [[akk|sagt]] {{akk|m||Regen}} und {{akk|m|stark[en]|Wind}} '
                 'voraus. [[dat|Am]] {{dat|m||Mittag}} steigt {{nom|f|D[ie]|Temperatur}} [[akk|um]] {{akk|m|einig[e]|Grad}}.',
                 'Samir [[akk|nimmt]] {{akk|m|sein[en] groß[en]|Schirm}} [[dat|bei]] {{dat|m|d[em] '
                 'nass[en]|Spaziergang}} mit. [[dat|In]] {{dat|f|d[er]|Nacht}} kommt sogar {{nom|m|ein klein[er]|Sturm}}. [[dat|Im]] '
                 '{{dat|m||Winter}} [[akk|gibt]] es manchmal {{akk|m||Schnee}}; [[dat|im]] {{dat|m||Sommer}} ist es oft heiß. {{nom|m||Frühling}} und '
                 '{{nom|m||Herbst}} sind für Samir {{nom|f|d[ie] interessantest[en]|Jahreszeiten}}. Er mag {{akk|f|jed[e]|Jahreszeit}} auf ihre eigene Weise.',
                 '[[dat|Am]] {{dat|n||Wochenende}} plant er je [[dat|nach]] {{dat|n||Wetter}}. ((Während|while)) einer kalten '
                 '<<f|Woche>> bleibt er öfter zu Hause, in {{dat|m|ein[em] warm[en]|Monat}} ist er mehr draußen. Nach '
                 '{{dat|n|ein[em]|Jahr}} versteht er besser, wie unterschiedlich {{nom|m||Morgen}}, {{nom|m||Mittag}}, '
                 '{{nom|m||Abend}} und {{nom|f||Nacht}} sein können.',
                 '[[dat|Im]] April ist {{nom|n|d[as]|Wetter}} besonders wechselhaft.\n'
                 '{{nom|f|D[ie]|Vorhersage}} stimmt nicht immer, und {{nom|m|d[er]|Durchschnitt}} sagt wenig '
                 '[[akk|über]] {{akk|m|ein[en] einzeln[en]|Tag}}.\n'
                 '{{nom|m|Groß[e]|Temperaturunterschiede}} können [[akk|beeinflussen]] {{akk|m|d[en]|Tagesplan}}.\n'
                 'Deshalb versucht Samir, sich gut vorzubereiten.\n'
                 'Morgens [[akk|nimmt]] er {{akk|m|d[en] leicht[en]|Mantel}} mit; mittags braucht er ihn oft nicht '
                 'mehr.\n'
                 'Dazu [[akk|trägt]] er {{akk|m|ein[en] wasserdicht[en]|Schuh}} und {{akk|f|ein[e] warm[e]|Socke}}; '
                 '{{nom|f|d[ie]|Farbe}} seiner Jacke passt gut [[dat|zum]] {{dat|m|grau[en]|Himmel}}.\n'
                 'Wenn es regnet, wartet er kurz [[dat|in]] {{dat|n|ein[em]|Café}}.\n'
                 '[[dat|Bei]] {{dat|f||Sonne}} geht er lieber zu Fuß.'],
  'b1': ['wechselhaft', 'Vorhersage', 'Durchschnitt', 'Temperaturunterschied', 'beeinflussen', 'sich vorbereiten'],
  'recall': [('Akkusativ von „sein großer Schirm“?', 'seinen großen Schirm.'),
             ('Dativ nach „bei“?', 'bei dem nassen Spaziergang / beim nassen Spaziergang.'),
             ('Artikel von „Wetter“?', 'das Wetter.'),
             ('Dativ von „der graue Himmel“?', 'dem grauen Himmel.'),
             ('Welche Jahreszeit ist feminin?',
              'die Jahreszeit; die einzelnen Namen Frühling/Sommer/Herbst/Winter sind maskulin.')]},
 {'number': 14,
  'title': 'Ein Tag in der Stadt',
  'targets': [('f', 'Stadt', 'city'),
              ('n', 'Dorf', 'village'),
              ('n', 'Zentrum', 'center'),
              ('n', 'Museum', 'museum'),
              ('n', 'Theater', 'theater'),
              ('f', 'Bibliothek', 'library'),
              ('f', 'Universität', 'university'),
              ('f', 'Schule', 'school'),
              ('n', 'Gebäude', 'building'),
              ('n', 'Denkmal', 'monument'),
              ('m', 'Garten', 'garden'),
              ('m', 'Zoo', 'zoo'),
              ('n', 'Stadion', 'stadium'),
              ('f', 'Geschichte', 'history/story'),
              ('f', 'Kultur', 'culture'),
              ('f', 'Kunst', 'art'),
              ('n', 'Bild', 'picture'),
              ('m', 'Künstler', 'male artist'),
              ('f', 'Künstlerin', 'female artist'),
              ('n', 'Konzert', 'concert'),
              ('f', 'Bühne', 'stage'),
              ('n', 'Publikum', 'audience'),
              ('f', 'Eintrittskarte', 'admission ticket'),
              ('f', 'Führung', 'guided tour'),
              ('f', 'Sehenswürdigkeit', 'sight/attraction')],
  'paragraphs': ['Samir und Lena fahren [[dat|mit]] {{dat|f|d[er]|Bahn}} in die Stadt; [[dat|nach]] '
                 '{{dat|f|d[er]|Ankunft}} [[akk|zeigt]] Lena ihm sofort {{akk|f|ihr[e]|Stadt}}. {{nom|n|D[as] modern[e]|Museum}} steht [[dat|im]] '
                 '{{dat|n||Zentrum}}, neben {{dat|n|ein[em] alt[en]|Theater}} und {{dat|f|ein[er] groß[en]|Bibliothek}}. [[dat|In]] '
                 '{{dat|f|d[er]|Nähe}} liegen {{nom|f||Universität}}, {{nom|f||Schule}} und {{nom|n|mehrere historisch[e]|Gebäude}}. Nicht weit '
                 'entfernt liegt {{nom|n|ein klein[es]|Dorf}}. [[dat|Am]] {{dat|n||Wochenende}} wollen sie auch {{akk|n|d[as]|Dorf}} besuchen.',
                 'Samir [[akk|besucht]] {{akk|f|ein[e] interessant[e]|Führung}} [[dat|in]] {{dat|n|d[em] '
                 'neu[en]|Museum}}. Er [[akk|sieht]] {{akk|n|ein|Denkmal}}, {{akk|n|viel[e]|Bilder}} und {{akk|f|modern[e]|Kunst}}. '
                 '{{nom|m|Ein|Künstler}} [[akk|erklärt]] {{akk|f|sein[e]|Arbeit}}; {{nom|f|Ein[e]|Künstlerin}} spricht [[akk|über]] {{akk|f||Kultur}} und '
                 '{{akk|f||Geschichte}}. Sie benutzt {{akk|f|ein[e] gehoben[e]|Sprache}} [[dat|mit]] {{dat|m|lang[en]|Sätzen}}, '
                 'aber Samir versteht jedes wichtige {{akk|n||Wort}}.',
                 'Später gehen beide [[akk|durch]] {{akk|m|ein[en]|Garten}}, [[dat|am]] {{dat|m||Zoo}} vorbei und '
                 '[[dat|zum]] {{dat|n||Stadion}}. [[dat|Am]] {{dat|m||Abend}} kaufen sie {{akk|f||Eintrittskarten}} [[akk|für]] '
                 '{{akk|n|ein|Konzert}}; {{nom|f|ein[e]|Eintrittskarte}} kostet nur wenig. [[dat|Auf]] {{dat|f|d[er]|Bühne}} spielt '
                 '{{nom|f|ein[e] klein[e]|Gruppe}}, und {{nom|n|D[as]|Publikum}} hört '
                 'aufmerksam zu. ((Dadurch|as a result/by doing so)) lernt Samir nicht nur {{akk|f|d[ie]|Sehenswürdigkeiten}}, '
                 'sondern auch {{akk|f|d[ie]|Kultur}} der Stadt besser kennen. {{nom|f|Dies[e]|Sehenswürdigkeit}} gefällt ihm besonders gut.',
                 '{{nom|m|D[er] kulturell[e]|Tag}} macht Samir neugierig.\n'
                 '[[dat|Im]] {{dat|n||Museum}} beginnt gerade {{nom|f|ein[e] neu[e]|Ausstellung}}, und [[dat|am]] '
                 '{{dat|m||Abend}} gibt es {{akk|f|ein[e] öffentlich[e]|Veranstaltung}}. {{nom|m|D[er]|Eintritt}} [[akk|für]] '
                 '{{akk|f|d[ie]|Ausstellung}} kostet leider extra.\n'
                 '{{akk|n|Einig[e]|Bilder}} [[akk|findet]] er wirklich beeindruckend.\n'
                 'Lena erklärt, warum {{nom|n|d[as]|Viertel}} kulturell wichtig ist.\n'
                 '[[akk|Für]] {{akk|m||Studierende}} gibt es {{akk|f|ein[e]|Eintrittsermäßigung}}.\n'
                 'Samir beginnt, sich stärker [[akk|für]] {{akk|f||Kunst}} zu interessieren.\n'
                 'Er spricht [[dat|mit]] {{dat|m|ein[em] jung[en]|Künstler}} und fragt [[dat|nach]] '
                 '{{dat|n|ein[em]|Bild}}.\n'
                 'Später [[akk|besucht]] er {{akk|f|d[ie]|Bibliothek}} und leiht {{akk|n|ein einfach[es]|Buch}} '
                 '[[akk|über]] {{akk|f|d[ie]|Stadtgeschichte}} aus.'],
  'b1': ['Ausstellung', 'Veranstaltung', 'beeindruckend', 'kulturell', 'Eintrittsermäßigung', 'sich interessieren'],
  'recall': [('Akkusativ von „eine interessante Führung“?', 'eine interessante Führung.'),
             ('Dativ von „das neue Museum“?', 'dem neuen Museum.'),
             ('Was triggert hier den Dativ?', '„in“ bei Ort (Wo?) → Dativ.'),
             ('Artikel von „Bühne“?', 'die Bühne.'),
             ('Dativ von „der Künstler“?', 'dem Künstler.')]},
 {'number': 15,
  'title': 'Ein technisches Problem',
  'targets': [('n', 'Internet', 'internet'),
              ('f', 'Webseite', 'website'),
              ('f', 'App', 'app'),
              ('n', 'Programm', 'program'),
              ('f', 'Datei', 'file'),
              ('m', 'Ordner', 'folder'),
              ('n', 'Passwort', 'password'),
              ('m', 'Benutzername', 'username'),
              ('n', 'Konto', 'account'),
              ('n', 'Video', 'video'),
              ('f', 'Kamera', 'camera'),
              ('n', 'Handy', 'mobile phone'),
              ('n', 'Smartphone', 'smartphone'),
              ('m', 'Laptop', 'laptop'),
              ('n', 'Tablet', 'tablet'),
              ('m', 'Chat', 'chat'),
              ('n', 'Netzwerk', 'network'),
              ('n', 'WLAN', 'Wi-Fi'),
              ('n', 'Kabel', 'cable'),
              ('m', 'Stecker', 'plug'),
              ('m', 'Akku', 'rechargeable battery'),
              ('f', 'Batterie', 'battery'),
              ('n', 'Ladegerät', 'charger'),
              ('m', 'Kopfhörer', 'headphones'),
              ('m', 'Lautsprecher', 'speaker')],
  'paragraphs': ['Eines Abends funktioniert {{nom|n|D[as]|Internet}} nicht. {{nom|m|D[er] alt[e]|Laptop}} [[akk|findet]] '
                 '{{akk|n|d[as]|WLAN}} nicht, und auch {{nom|n|D[as]|Smartphone}} [[akk|hat]] {{akk|f|kein[e]|Verbindung}}. '
                 'Samir [[akk|öffnet]] {{akk|f|ein[e]|App}}, '
                 '{{akk|f|ein[e]|Webseite}} und später {{akk|n|ein|Programm}}, aber nichts hilft.',
                 'Er [[akk|prüft]] {{akk|n|d[as] lang[e]|Kabel}} [[dat|an]] {{dat|m|d[em] locker[en]|Stecker}}. Danach '
                 'lädt er {{akk|m|d[en]|Akku}} [[dat|mit]] {{dat|n|ein[em]|Ladegerät}}. Auf {{dat|n|d[em]|Tablet}} '
                 '[[akk|öffnet]] er {{akk|m|ein[en]|Ordner}}, {{akk|f|ein[e]|Datei}} und {{akk|n|ein|Video}}. {{nom|f|D[ie]|Kamera}} '
                 'funktioniert, aber {{nom|m|D[er]|Lautsprecher}} bleibt still.',
                 '{{nom|m|Ein|Satz}} aus der Chat-Nachricht ist schwer zu verstehen; eine App hilft [[dat|mit]] '
                 '{{dat|f|d[er]|Sprache}} und erklärt [[dat|in]] {{dat|n|ein[em]|Wort}}, was gemeint ist. '
                 '[[dat|Im]] {{dat|m||Chat}} fragt Samir {{akk|m|ein[en]|Kollegen}} [[dat|nach]] {{dat|f||Hilfe}}. Dieser erklärt, dass '
                 '{{nom|m||Benutzername}}, {{nom|n||Passwort}} und {{nom|n||Konto}} korrekt sind. Schließlich [[akk|startet]] Samir '
                 '{{akk|n|d[as]|Netzwerk}} neu. '
                 '((Nachdem|after)) {{nom|n|D[as]|WLAN}} wieder da ist, [[akk|verbindet]] er {{akk|m||Kopfhörer}} und {{akk|n||Handy}} '
                 '[[akk|ohne]] {{akk|n||Problem}}. {{akk|f|D[ie]|Batterie}} der kleinen Maus muss er trotzdem bald [[akk|wechseln]].',
                 '[[dat|Nach]] {{dat|n|d[em]|WLAN-Problem}} möchte Samir {{akk|m|sein[en]|Laptop}} besser '
                 'organisieren.\n'
                 'Er muss zuerst {{akk|n|einig[e]|Programme}} [[akk|aktualisieren]] und {{akk|f|wichtig[e]|Dateien}} [[akk|speichern]].\n'
                 '[[dat|In]] {{dat|f|d[en]|Einstellungen}} ändert er {{akk|n|d[as]|Passwort}} und liest '
                 '{{akk|m|ein[en] kurz[en]|Hinweis}} [[dat|zum]] {{dat|m||Datenschutz}}.\n'
                 '[[dat|Am]] {{dat|m||Abend}} gibt es noch {{akk|f|ein[e] klein[e]|Störung}}; deshalb muss er '
                 '{{akk|f|ein[e]|App}} neu installieren.\n'
                 'Er [[akk|verbindet]] {{akk|n|d[as] neu[e]|Ladegerät}} [[dat|mit]] {{dat|m|d[em]|Laptop}} und [[akk|prüft]] '
                 'danach {{akk|f||Kamera}} und {{akk|m||Kopfhörer}}.\n'
                 'Jetzt funktioniert alles wieder.'],
  'b1': ['aktualisieren', 'speichern', 'Einstellungen', 'Datenschutz', 'Störung', 'installieren'],
  'recall': [('Akkusativ von „das lange Kabel“?', 'das lange Kabel.'),
             ('Dativ: an ___ lockeren Stecker', 'an dem lockeren Stecker.'),
             ('Artikel von „Laptop“?', 'der Laptop.'),
             ('Was ist neutrum: App oder Programm?', 'das Programm.'),
             ('Dativ von „die Batterie“?', 'der Batterie.')]},
 {'number': 16,
  'title': 'Urlaub am Meer',
  'targets': [('m', 'Strand', 'beach'),
              ('n', 'Meer', 'sea'),
              ('f', 'Insel', 'island'),
              ('m', 'Berg', 'mountain'),
              ('n', 'Tal', 'valley'),
              ('m', 'See', 'lake'),
              ('m', 'Campingplatz', 'campsite'),
              ('n', 'Zelt', 'tent'),
              ('f', 'Unterkunft', 'accommodation'),
              ('f', 'Pension', 'guesthouse'),
              ('m', 'Balkon', 'balcony'),
              ('f', 'Terrasse', 'terrace'),
              ('f', 'Aussicht', 'view'),
              ('n', 'Handtuch', 'towel'),
              ('f', 'Dusche', 'shower'),
              ('m', 'Pool', 'pool'),
              ('n', 'Buffet', 'buffet'),
              ('m', 'Service', 'service'),
              ('n', 'Personal', 'staff'),
              ('f', 'Zimmerkarte', 'room key card'),
              ('f', 'Buchung', 'booking'),
              ('n', 'Reisebüro', 'travel agency'),
              ('m', 'Ausflug', 'excursion'),
              ('n', 'Boot', 'boat'),
              ('m', 'Hafen', 'harbor')],
  'paragraphs': ['[[dat|Im]] {{dat|m||Sommer}} fahren Samir und Lena [[akk|ans]] {{akk|n||Meer}}. {{nom|m|D[er] breit[e]|Strand}} liegt '
                 'direkt [[dat|vor]] {{dat|f|ihr[er]|Pension}}. Von {{dat|m|d[em]|Balkon}} [[akk|sehen]] sie {{akk|n|d[as]|Meer}}, {{akk|f|ein[e] klein[e]|Insel}} und weit hinten {{akk|m|ein[en]|Berg}}.',
                 '[[dat|Am]] {{dat|m|erst[en]|Tag}} [[akk|buchen]] sie {{akk|m|ein[en] kurz[en]|Ausflug}} [[dat|bei]] {{dat|n|d[em] '
                 'lokal[en]|Reisebüro}}. {{nom|f|D[ie]|Buchung}} ist schnell erledigt; sie bestätigen {{akk|f|d[ie]|Buchung}} '
                 'per E-Mail. [[dat|Mit]] {{dat|n|ein[em]|Boot}} fahren sie [[dat|vom]] {{dat|m||Hafen}} [[dat|zu]] {{dat|f|ein[er] ruhig[en]|Bucht}}. '
                 'Später sitzen sie [[dat|auf]] {{dat|f|d[er]|Terrasse}} ihrer Unterkunft und [[akk|genießen]] {{akk|f|d[ie]|Aussicht}}.',
                 '[[dat|In]] {{dat|f|d[er]|Pension}} [[akk|gibt]] es {{akk|m||Pool}}, {{akk|f||Dusche}}, {{akk|n||Handtuch}}, {{akk|f||Zimmerkarte}} und morgens '
                 '{{akk|n|ein|Buffet}}. {{nom|n|D[as]|Personal}} ist freundlich, und {{nom|m|D[er]|Service}} ist schnell. Am Pool '
                 'bestellen sie sich noch {{akk|n|ein kühl[es]|Getränk}}. [[akk|Für]] {{akk|f|zwei|Nächte}} überlegen sie sogar, auf {{dat|m|ein[em]|Campingplatz}} in {{dat|n|ein[em]|Zelt}} zu '
                 'schlafen. ((Allerdings|however)) entscheiden sie sich am Ende [[akk|für]] {{akk|f|d[ie] '
                 'bequemer[e]|Unterkunft}}. [[dat|Auf]] {{dat|m|d[em]|Rückweg}} [[akk|sehen]] sie {{akk|m|ein[en]|See}} und {{akk|n|ein grün[es]|Tal}}.',
                 '{{nom|m|D[er]|Urlaub}} [[akk|bringt]] echte Erholung.\n'
                 'Samir und Lena fahren {{akk|m|ein[en]|Tag}} [[dat|an]] {{dat|f|d[er]|Küste}} entlang und sehen '
                 '{{akk|f|ein[e] offen[e]|Landschaft}} [[dat|mit]] kleinen Dörfern.\n'
                 '[[dat|In]] {{dat|n|ein[em] klein[en]|Dorf}} probieren sie lokalen Fisch.\n'
                 '[[dat|Unter]] {{dat|f|ein[er] einzeln[en]|Wolke}} bleibt es trotzdem warm, denn [[dat|in]] '
                 '{{dat|f|dies[er]|Jahreszeit}} ist das Wetter mild.\n'
                 '[[dat|Bei]] {{dat|f|ein[er] besonder[en]|Sehenswürdigkeit}} machen sie viele Fotos; Samir hält '
                 '[[dat|an]] {{dat|f|dies[er]|Erinnerung}} noch lange fest.\n'
                 '[[dat|Am]] {{dat|m||Nachmittag}} können sie sich [[dat|am]] {{dat|m||Strand}} entspannen.\n'
                 '{{nom|n|Ein lokal[es]|Café}} ist besonders empfehlenswert.\n'
                 'Später steigen sie [[dat|zu]] {{dat|m|ein[em]|Aussichtspunkt}} [[dat|über]] {{dat|m|d[em]|Hafen}} '
                 'hinauf.\n'
                 'Von dort [[akk|sehen]] sie {{akk|n|d[as] ruhig[e]|Meer}} und viele kleine Boote.\n'
                 '[[dat|Am]] {{dat|m||Abend}} planen sie {{akk|m|kein[en] fest[en]|Termin}}, sondern entscheiden spontan.'],
  'b1': ['Erholung', 'Küste', 'Landschaft', 'entspannen', 'empfehlenswert', 'Aussichtspunkt'],
  'recall': [('Akkusativ von „ein kurzer Ausflug“?', 'einen kurzen Ausflug.'),
             ('Dativ nach „bei“?', 'bei dem lokalen Reisebüro / beim lokalen Reisebüro.'),
             ('Artikel von „Unterkunft“?', 'die Unterkunft.'),
             ('Dativ von „der breite Strand“?', 'dem breiten Strand.'),
             ('Warum ist „Meer“ grün?', 'das Meer → neutrum.')]},
 {'number': 17,
  'title': 'Wanderung im Grünen',
  'targets': [('f', 'Natur', 'nature'),
              ('m', 'Wald', 'forest'),
              ('m', 'Baum', 'tree'),
              ('f', 'Blume', 'flower'),
              ('f', 'Pflanze', 'plant'),
              ('n', 'Gras', 'grass'),
              ('n', 'Feld', 'field'),
              ('f', 'Wiese', 'meadow'),
              ('m', 'Hügel', 'hill'),
              ('m', 'Pfad', 'path'),
              ('m', 'Bach', 'stream'),
              ('m', 'Vogel', 'bird'),
              ('n', 'Tier', 'animal'),
              ('m', 'Hund', 'dog'),
              ('f', 'Katze', 'cat'),
              ('n', 'Pferd', 'horse'),
              ('f', 'Kuh', 'cow'),
              ('n', 'Schaf', 'sheep'),
              ('m', 'Bauernhof', 'farm'),
              ('m', 'Bauer', 'farmer'),
              ('f', 'Bäuerin', 'female farmer'),
              ('f', 'Umwelt', 'environment'),
              ('m', 'Müll', 'trash'),
              ('n', 'Papier', 'paper'),
              ('n', 'Plastik', 'plastic')],
  'paragraphs': ['[[dat|Nach]] {{dat|m|d[em]|Urlaub}} machen Samir und Lena {{akk|f|ein[e]|Wanderung}}. [[dat|An]] {{dat|m|d[em]|Schuh}} und '
                 '[[dat|an]] {{dat|f|d[er]|Socke}} merkt Samir, wie gut die Ausrüstung war. {{nom|f|D[ie] '
                 'nächst[e]|Buchung}} ist schon geplant; bald machen sie {{akk|f|ein[e] neu[e]|Buchung}} [[akk|für]] {{akk|m|d[en]|Herbst}}. '
                 '{{nom|m|D[er] dicht[e]|Wald}} beginnt hinter '
                 '{{dat|m|ein[em]|Bauernhof}}. [[dat|Auf]] {{dat|f|d[er]|Wiese}} stehen {{nom|f||Kühe}}, {{nom|n||Schafe}} und {{nom|n|ein|Pferd}}. '
                 '{{nom|m|Ein|Hund}} läuft [[dat|neben]] {{dat|m|d[em]|Bauern}}, {{nom|f|Ein[e]|Katze}} sitzt [[dat|bei]] {{dat|f|d[er]|Bäuerin}}.',
                 'Samir [[akk|folgt]] {{akk|m|d[en] schmal[en]|Pfad}}. Danach gehen beide [[akk|durch]] {{akk|f|d[ie] '
                 'ruhig[e]|Natur}}. Später laufen sie [[dat|an]] {{dat|m|ein[em]|Bach}} entlang, vorbei an {{dat|m||Bäumen}}, '
                 '{{dat|f||Blumen}}, {{dat|f||Pflanzen}}, {{dat|n||Gras}} und {{dat|n|ein[em]|Feld}}. {{nom|m|D[er]|Weg}} führt langsam auf {{akk|m|ein[en]|Hügel}}.',
                 'Auf {{dat|m|ein[em]|Hügel}} beobachten sie {{akk|m|ein[en]|Vogel}} und {{akk|n|ein ander[es]|Tier}}. '
                 '{{nom|m|Ein hoh[er]|Baum}} spendet Schatten; Lena pflückt {{akk|f|ein[e]|Blume}} für Samir, und '
                 '{{nom|f|d[ie]|Pflanze}} daneben blüht schön. Unten sehen sie {{akk|f|ein[e]|Kuh}} und nähern sich '
                 '{{dat|n|ein[em]|Schaf}}. [[dat|Beim]] {{dat|n||Picknick}} '
                 '[[akk|sammeln]] sie {{akk|n||Papier}} und {{akk|n||Plastik}} ein, damit {{nom|m|kein|Müll}} liegen bleibt. '
                 '((Während|while)) sie zurückgehen, sprechen sie [[akk|über]] {{akk|f||Umwelt}} und {{akk|f||Natur}}. {{nom|m|D[er]|Tag}} endet '
                 'ruhig und ohne Eile.',
                 '[[dat|Beim]] Wandern sprechen Samir und Lena [[akk|über]] {{akk|m||Umweltschutz}}.\n'
                 '[[dat|Auf]] {{dat|m|d[em]|Bauernhof}} wird {{nom|n||Papier}} getrennt und {{nom|n||Plastik}} '
                 'gesammelt.\n'
                 '{{akk|n|Einig[e]|Materialien}} kann man [[akk|recyceln]].\n'
                 '{{nom|m|D[er]|Bauer}} erklärt, warum {{nom|m|ein nachhaltig[er]|Umgang}} [[dat|mit]] '
                 '{{dat|n||Wasser}} wichtig ist und wie man {{akk|n||Tiere}} und {{akk|f||Pflanzen}} [[akk|schützen]] kann.\n'
                 '{{nom|m|Zu viel|Müll}} führt [[dat|zu]] {{dat|f||Verschmutzung}}.\n'
                 '{{nom|m||Besucher}} sollen deshalb {{akk|f||Rücksicht}} nehmen.\n'
                 'Samir [[akk|sammelt]] {{akk|n|d[as] alt[e]|Papier}} ein und trägt es [[dat|zum]] {{dat|m||Hof}} zurück.\n'
                 'Danach gehen beide ruhig [[dat|am]] {{dat|m||Bach}} entlang.'],
  'b1': ['Umweltschutz', 'recyceln', 'nachhaltig', 'schützen', 'Verschmutzung', 'Rücksicht nehmen'],
  'recall': [('Akkusativ von „der schmale Pfad“?', 'den schmalen Pfad.'),
             ('Welchen Fall verlangt „durch“ normalerweise?', 'Akkusativ.'),
             ('Dativ von „die ruhige Natur“?', 'der ruhigen Natur.'),
             ('Artikel von „Bauernhof“?', 'der Bauernhof.'),
             ('Warum ist „Tier“ grün?', 'das Tier → neutrum.')]},
 {'number': 18,
  'title': 'Eine kleine Feier',
  'targets': [('f', 'Party', 'party'),
              ('n', 'Fest', 'festival/celebration'),
              ('m', 'Tanz', 'dance'),
              ('n', 'Lied', 'song'),
              ('m', 'Freund', 'male friend'),
              ('f', 'Freundin', 'female friend'),
              ('m', 'Bekannter', 'male acquaintance'),
              ('f', 'Bekannte', 'female acquaintance'),
              ('f', 'Gruppe', 'group'),
              ('n', 'Gespräch', 'conversation'),
              ('m', 'Witz', 'joke'),
              ('n', 'Lachen', 'laughter'),
              ('f', 'Stimmung', 'mood/atmosphere'),
              ('f', 'Dekoration', 'decoration'),
              ('f', 'Kerze', 'candle'),
              ('m', 'Kuchen', 'cake'),
              ('f', 'Torte', 'cake/torte'),
              ('m', 'Ballon', 'balloon'),
              ('f', 'Überraschung', 'surprise'),
              ('m', 'Wunsch', 'wish'),
              ('m', 'Gruß', 'greeting'),
              ('m', 'Anlass', 'occasion'),
              ('m', 'Abschluss', 'completion/graduation'),
              ('m', 'Erfolg', 'success'),
              ('m', 'Treffpunkt', 'meeting point')],
  'paragraphs': ['[[dat|Nach]] {{dat|m|einig[en]|Monaten}} [[akk|besteht]] Samir {{akk|m|ein[en] wichtig[en]|Kurs}}. Lena '
                 '[[akk|organisiert]] {{akk|f|ein[e] klein[e]|Party}}. '
                 '{{nom|f|D[ie] gut[e]|Stimmung}} beginnt schon [[dat|am]] {{dat|m||Nachmittag}}. Für Samir ist {{nom|n|d[as]|Fest}} '
                 'etwas ganz Besonderes. {{nom|m||Freunde}}, {{nom|f||Freundinnen}} und {{nom|f||Bekannte}} kommen. Auch '
                 '{{nom|m|ein|Bekannter}} aus dem Kurs bringt {{akk|f|ein[e] klein[e]|Gruppe}} von Kollegen mit. '
                 'Samir [[akk|begrüßt]] {{akk|m|d[en]|Bekannten}} herzlich und umarmt {{akk|f|sein[e] best[e]|Freundin}}. '
                 'Später feiern alle {{akk|n|d[as]|Fest}} bis spät [[akk|in]] {{akk|f|d[ie]|Nacht}}. Auch sein alter Deutschlehrer kommt: '
                 'Samir [[akk|stellt]] {{akk|m|sein[en] alt[en]|Lehrer}} den Freunden vor. {{nom|m|Ein|Freund}} bringt '
                 '{{akk|m|sein[en]|Sohn}} und {{akk|f|sein[e]|Tochter}} mit, aber er vermisst {{akk|f|sein[e]|Ehefrau}}, '
                 'die zu Hause bleibt.',
                 'Überall stehen {{nom|f||Blumen}}, und Lena bringt noch {{akk|f|ein[e]|Pflanze}} mit. Lena [[akk|stellt]] {{akk|f|d[ie] bunt[e]|Dekoration}} [[dat|neben]] {{dat|f|d[ie] groß[e]|Torte}}. '
                 '[[dat|Auf]] {{dat|m|d[em]|Tisch}} stehen {{nom|m||Kuchen}} und {{nom|f||Kerzen}}; [[dat|an]] {{dat|f|d[er]|Wand}} hängen {{nom|m||Ballons}}. Lena '
                 '[[akk|zündet]] {{akk|f|ein[e]|Kerze}} an. Jemand [[akk|spielt]] {{akk|n|ein|Lied}}, später [[akk|gibt]] es {{akk|m||Tanz}}, '
                 '{{akk|m||Witze}} und viel {{akk|n||Lachen}}. {{nom|m|Ein gut[er]|Witz}} macht alle froh.',
                 'Samir spricht in {{dat|n|ein[em] lang[en]|Gespräch}} [[akk|über]] {{akk|m|sein[en]|Abschluss}} und '
                 '{{akk|m|d[en]|Erfolg}}. Er bedankt sich [[akk|für]] {{akk|m|jed[en]|Gruß}} und {{akk|m|jed[en]|Wunsch}}. '
                 '((Weil|because)) {{nom|m|D[er]|Anlass}} für ihn wichtig ist, merkt er sich {{akk|m|d[en]|Treffpunkt}} und '
                 '{{akk|m|d[ie]|Menschen}} besonders gut. {{nom|f|D[ie]|Überraschung}} ist gelungen.',
                 '{{nom|f|D[ie]|Feier}} bleibt Samir lange [[dat|im]] {{dat|n||Gedächtnis}}.\n'
                 '{{nom|m|D[er]|Abend}} ist wirklich gelungen.\n'
                 'Er möchte sich [[dat|bei]] Lena [[akk|für]] {{akk|f|d[ie]|Organisation}} bedanken.\n'
                 '{{nom|m|D[ie]|Gäste}} unterhalten sich bis spät [[akk|in]] {{akk|f|d[ie]|Nacht}}, und [[akk|für]] Samir wird '
                 '{{nom|f|d[ie]|Party}} [[dat|zu]] {{dat|n|ein[em] besonder[en]|Erlebnis}}.\n'
                 '[[dat|Auf]] {{dat|f|d[er] ursprünglich[en]|Einladung}} stand nur „kleine Feier“, aber '
                 '{{nom|f|d[ie]|Stimmung}} ist fast feierlich.\n'
                 'Samir [[dat|dankt]] {{dat|m|sein[en] gut[en]|Freunden}} und [[akk|zeigt]] ihnen später {{akk|n|einig[e]|Fotos}}.\n'
                 '[[dat|Am]] {{dat|m|nächst[en]|Morgen}} [[akk|findet]] er noch {{akk|m|ein[en]|Ballon}} [[dat|unter]] '
                 '{{dat|m|d[em]|Tisch}}.'],
  'b1': ['gelungen', 'sich bedanken', 'unterhalten', 'Erlebnis', 'Einladung', 'feierlich'],
  'recall': [('Akkusativ von „die bunte Dekoration“?', 'die bunte Dekoration.'),
             ('Dativ nach „neben“ bei Ort (Wo?)?', 'neben der großen Torte.'),
             ('Artikel von „Lachen“?', 'das Lachen.'),
             ('Dativ von „der Erfolg“?', 'dem Erfolg.'),
             ('Was ist der Artikel von „Treffpunkt“?', 'der Treffpunkt.')]},
 {'number': 19,
  'title': 'Reparatur zu Hause',
  'targets': [('n', 'Problem', 'problem'),
              ('f', 'Reparatur', 'repair'),
              ('m', 'Handwerker', 'male tradesperson'),
              ('f', 'Handwerkerin', 'female tradesperson'),
              ('n', 'Werkzeug', 'tool'),
              ('m', 'Hammer', 'hammer'),
              ('f', 'Schraube', 'screw'),
              ('m', 'Nagel', 'nail'),
              ('f', 'Bohrmaschine', 'drill'),
              ('f', 'Wand', 'wall'),
              ('m', 'Boden', 'floor'),
              ('f', 'Decke', 'ceiling/blanket'),
              ('f', 'Heizung', 'heating'),
              ('m', 'Strom', 'electricity'),
              ('n', 'Licht', 'light'),
              ('m', 'Wasserhahn', 'faucet/tap'),
              ('n', 'Rohr', 'pipe'),
              ('f', 'Maschine', 'machine'),
              ('f', 'Waschmaschine', 'washing machine'),
              ('m', 'Kühlschrank', 'refrigerator'),
              ('m', 'Herd', 'stove'),
              ('m', 'Ofen', 'oven'),
              ('n', 'Gerät', 'device/appliance'),
              ('m', 'Schaden', 'damage'),
              ('m', 'Notfall', 'emergency')],
  'paragraphs': ['Eines Morgens gibt es {{akk|n|ein|Problem}} [[dat|in]] {{dat|f|d[er]|Wohnung}}. {{nom|m|D[er] alt[e]|Wasserhahn}} tropft, '
                 'und später funktioniert auch {{nom|f|D[ie]|Heizung}} nicht richtig. Samir [[akk|ruft]] {{akk|f|ein[e]|Handwerkerin}} an. '
                 '[[akk|Durch]] {{akk|n|d[as]|Fenster}} [[akk|sieht]] er {{akk|m|ein[en] hoh[en]|Baum}} und schaut {{dat|f|ein[er]|Kuh}} '
                 'beim Grasen zu; {{nom|n|Ein|Schaf}} schaut neugierig herüber.',
                 '[[dat|In]] {{dat|f|ein[er] kurz[en]|Pause}} [[dat|telefoniert]] Samir [[dat|mit]] {{dat|f|d[er]|Freundin}} von der Party. '
                 'Sie erzählt {{akk|m|ein[en]|Witz}} über {{akk|m|ein[en]|Bekannten}} und fragt, ob {{nom|n|d[as]|Fest}} '
                 '{{akk|n|nächst[es]|Jahr}} wieder stattfindet; auch {{nom|m|d[er]|Arzt}} aus der Nachbarpraxis kommt kurz [[dat|zur]] '
                 '{{dat|f||Sprache}}. Samir '
                 'denkt an {{akk|m|d[en]|Patienten}} [[dat|im]] {{dat|n||Wartezimmer}} von damals.',
                 'Sie [[akk|öffnet]] {{akk|n|d[as] klein[e]|Gerät}} [[dat|mit]] {{dat|n|d[em] passend[en]|Werkzeug}}. '
                 '[[dat|In]] {{dat|m|ihr[em]|Koffer}} liegen {{nom|m||Hammer}}, {{nom|f||Schraube}}, {{nom|m||Nagel}} und {{nom|f|ein[e] klein[e]|Bohrmaschine}}. '
                 'Sie [[akk|prüft]] {{akk|f||Wand}}, {{akk|m||Boden}}, {{akk|f||Decke}}, {{akk|m||Strom}}, {{akk|n||Licht}} und {{akk|n|ein|Rohr}}.',
                 '[[dat|In]] {{dat|f|d[er]|Küche}} schaut sie auch [[dat|nach]] {{dat|m||Kühlschrank}}, {{dat|m||Herd}} und {{dat|m||Ofen}}; [[dat|im]] '
                 '{{dat|n||Bad}} [[akk|prüft]] sie {{akk|f|d[ie]|Waschmaschine}}. Zum Glück ist {{nom|m|D[er]|Schaden}} klein und {{nom|m|kein|Notfall}}. '
                 '((Nachdem|after)) {{nom|f|D[ie]|Reparatur}} fertig ist, zeigt {{nom|f|D[ie]|Handwerkerin}} Samir, was er '
                 '[[dat|beim]] {{dat|n|nächst[en]|Problem}} selbst prüfen kann. [[akk|Für]] {{akk|f|d[ie]|Heizung}} ruft sie noch '
                 '{{akk|m|ein[en]|Handwerker}} von der Firma an. {{nom|f|D[ie]|Maschine}} läuft wieder ruhig.',
                 '[[dat|Nach]] {{dat|f|d[er]|Reparatur}} erklärt {{nom|f|d[ie]|Handwerkerin}}, wie Samir {{akk|n||Geräte}} selbst '
                 '[[akk|überprüfen]] kann. {{nom|m|D[er]|Handwerker}} von der Firma kommt beim nächsten Mal noch schneller vorbei.\n'
                 '{{akk|m|Manch[e]|Teile}} muss {{nom|m|ein|Fachbetrieb}} [[akk|austauschen]], besonders wenn {{nom|n|ein|Kabel}} sichtbar '
                 'beschädigt ist.\n'
                 '[[akk|Für]] {{akk|m|d[en]|Kühlschrank}} gibt es noch {{akk|f|ein[e]|Garantie}}.\n'
                 '[[dat|Bei]] {{dat|n|ein[em] größer[en]|Problem}} sollte Samir trotzdem {{akk|m|ein[en]|Fachmann}} '
                 'rufen und vorsichtshalber {{akk|m|d[en]|Strom}} ausschalten.\n'
                 'Er [[dat|zeigt]] {{dat|f|d[er] erfahren[en]|Handwerkerin}} auch {{akk|m|d[en] alt[en]|Herd}}.\n'
                 'Diesmal ist dort aber alles in Ordnung.'],
  'b1': ['überprüfen', 'austauschen', 'beschädigt', 'Garantie', 'Fachmann', 'vorsichtshalber'],
  'recall': [('Dativ nach „mit“?', 'mit dem passenden Werkzeug.'),
             ('Akkusativ von „das kleine Gerät“?', 'das kleine Gerät.'),
             ('Artikel von „Bohrmaschine“?', 'die Bohrmaschine.'),
             ('Dativ von „der alte Wasserhahn“?', 'dem alten Wasserhahn.'),
             ('Welche Form: mit ___ kleinen Schraube?', 'mit der kleinen Schraube.')]},
 {'number': 20,
  'title': 'Der nächste Schritt – Brücke zu B1',
  'targets': [('f', 'Zukunft', 'future'),
              ('f', 'Möglichkeit', 'possibility'),
              ('f', 'Entscheidung', 'decision'),
              ('f', 'Erfahrung', 'experience'),
              ('f', 'Ausbildung', 'training/education'),
              ('m', 'Beruf', 'profession'),
              ('f', 'Bewerbung', 'application'),
              ('m', 'Lebenslauf', 'CV/résumé'),
              ('f', 'Stelle', 'job/position'),
              ('f', 'Karriere', 'career'),
              ('n', 'Ziel', 'goal'),
              ('f', 'Chance', 'chance/opportunity'),
              ('f', 'Veränderung', 'change'),
              ('f', 'Verantwortung', 'responsibility'),
              ('f', 'Idee', 'idea'),
              ('f', 'Lösung', 'solution'),
              ('f', 'Meinung', 'opinion'),
              ('m', 'Grund', 'reason'),
              ('m', 'Vorteil', 'advantage'),
              ('m', 'Nachteil', 'disadvantage'),
              ('f', 'Entwicklung', 'development'),
              ('m', 'Fortschritt', 'progress'),
              ('f', 'Planung', 'planning'),
              ('n', 'Ergebnis', 'result'),
              ('f', 'Hoffnung', 'hope')],
  'paragraphs': ['{{akk|n|Ein|Jahr}} [[dat|nach]] {{dat|m|sein[em]|Umzug}} denkt Samir [[akk|über]] {{akk|f|d[ie]|Zukunft}} nach. {{nom|f|D[ie] '
                 'nächst[e]|Entscheidung}} [[akk|betrifft]] {{akk|m|sein[en]|Beruf}}. Er [[akk|hat]] mehr {{akk|f||Erfahrung}}, '
                 '{{akk|f|ein[e]|Ausbildung}} und {{akk|n|ein klar[es]|Ziel}}. {{nom|f|Ein[e] neu[e]|Stelle}} könnte {{nom|f|ein[e] gut[e]|Chance}} '
                 'sein.',
                 'Manchmal blickt er auch zurück. [[dat|Mit]] {{dat|m|d[em]|Apfel}} vom ersten Abendessen, '
                 '[[dat|mit]] {{dat|m|d[em]|Eintritt}} ins Schwimmbad, [[dat|mit]] {{dat|n|d[em]|Getränk}} im '
                 'Restaurant, [[dat|mit]] {{dat|f|d[er]|Eintrittskarte}} fürs Konzert, [[dat|mit]] '
                 '{{dat|f|d[er]|Kerze}} auf Lenas Party und [[dat|mit]] {{dat|m|d[em]|Handwerker}} verbindet Samir '
                 'kleine Geschichten. [[akk|An]] {{akk|f|d[ie]|Eintrittskarte}}, {{akk|f|d[ie]|Kerze}} und '
                 '{{akk|m|d[en]|Handwerker}} denkt er besonders gern zurück. {{nom|m|D[er] freundlich[e]|Kunde}} '
                 'aus dem Kaufhaus, {{nom|m|d[er]|Arzt}} und {{nom|m|d[er]|Patient}} von damals, sogar '
                 '{{nom|m|sein|Lehrer}} aus dem Kurs — an sie alle erinnert er sich gern. Auch {{akk|f|d[ie]|Farbe}} '
                 'des ersten Herbstes, {{akk|f|d[ie] frisch[en]|Kartoffeln}} und {{akk|f|d[ie]|Nudeln}} vom '
                 'gemeinsamen Essen [[akk|behält]] er [[dat|in]] {{dat|f|d[er]|Erinnerung}}. [[akk|Für]] '
                 '{{akk|f|jed[e]|Wolke}} am Himmel, {{akk|f|jed[e]|Jahreszeit}} und {{akk|n|jed[es]|Dorf}} unterwegs '
                 'hatte er ein offenes Auge, genauso [[akk|für]] {{akk|f|jed[e]|Sehenswürdigkeit}}, '
                 '{{akk|f|jed[e]|Blume}} und {{akk|f|jed[e]|Pflanze}} am Wegrand. Auch [[akk|an]] '
                 '{{akk|m|d[en]|Sohn}} und {{akk|f|d[ie]|Tochter}} seines Freundes denkt er zurück, ebenso '
                 '[[akk|an]] {{akk|f|d[ie]|Ehefrau}}, die damals zu Hause geblieben war. {{nom|m|D[er]|Baum}} vor '
                 'dem Fenster, {{nom|f|d[ie]|Kuh}} auf der Wiese und {{nom|n|d[as]|Schaf}} von nebenan bleiben ihm '
                 'ebenfalls im Kopf. [[dat|Bei]] {{dat|n|d[em]|Fest}}, [[dat|mit]] {{dat|m|d[em]|Bekannten}} aus dem '
                 'Kurs und [[dat|bei]] {{dat|m|d[em]|Witz}} von Lena hat er viel gelacht; auch '
                 '{{nom|f|sein[e]|Freundin}} war damals dabei.',
                 'Samir [[akk|schreibt]] {{akk|f|ein[e] neu[e]|Bewerbung}} [[dat|mit]] {{dat|m|sein[em] '
                 'aktuell[en]|Lebenslauf}}. Er spricht [[dat|mit]] {{dat|m||Freunden}} [[akk|über]] {{akk|f||Karriere}}, {{akk|f||Veränderung}} und '
                 '{{akk|f||Verantwortung}}. Jeder [[akk|hat]] {{akk|f|ein[e] ander[e]|Meinung}}, aber Samir [[akk|sucht]] {{akk|m|sein[en] eigen[en]|Grund}} '
                 '[[akk|für]] {{akk|f|d[ie]|Entscheidung}}.',
                 'Er [[akk|vergleicht]] {{akk|m||Vorteil}} und {{akk|m||Nachteil}}, [[akk|entwickelt]] {{akk|f|ein[e]|Idee}} und sucht [[dat|nach]] '
                 '{{dat|f|ein[er]|Lösung}}. ((Einerseits|on the one hand)) möchte er {{akk|f||Sicherheit}}, ((andererseits|on the '
                 'other hand)) möchte er {{akk|m||Fortschritt}}. {{nom|f|D[ie]|Planung}} dauert {{akk|f|mehrere|Wochen}}. '
                 '{{nom|n|D[as]|Ergebnis}} ist noch offen, aber {{nom|f|D[ie]|Hoffnung}} bleibt: [[dat|Mit]] {{dat|f|jed[er] neu[en]|Erfahrung}} '
                 'wächst {{nom|f|D[ie]|Möglichkeit}}, selbstbewusster zu handeln.',
                 '[[akk|Für]] Samir beginnt nun {{nom|f|d[ie]|Brücke}} [[dat|zu]] B1.\n'
                 'Er [[akk|schreibt]] {{akk|f|sein[e] erst[e] ernsthaft[e]|Bewerbung}} und denkt länger [[akk|über]] '
                 '{{akk|f|sein[e]|Karriere}} nach.\n'
                 '{{nom|f|D[ie]|Entscheidung}} ist nicht leicht, aber sie eröffnet {{akk|f|ein[e] '
                 'neu[e]|Möglichkeit}}.\n'
                 '[[dat|In]] {{dat|m|d[en] letzt[en]|Monaten}} hat er {{akk|f|ein[e] deutlich[e] '
                 'persönlich[e]|Entwicklung}} [[akk|erlebt]] und sieht jetzt {{akk|f|ein[e] neu[e]|Perspektive}}.\n'
                 'Er [[akk|schickt]] {{akk|f|d[ie] fertig[e]|Bewerbung}} ab und wartet [[akk|auf]] '
                 '{{akk|f|ein[e]|Antwort}}.\n'
                 'Unabhängig [[dat|vom]] {{dat|n||Ergebnis}} weiß er, dass regelmäßiges Lesen, Sprechen und '
                 'Wiederholen ihm weiterhelfen wird.'],
  'b1': ['Bewerbung', 'Karriere', 'Entscheidung', 'Möglichkeit', 'Entwicklung', 'Perspektive'],
  'recall': [('Akkusativ von „eine neue Bewerbung“?', 'eine neue Bewerbung.'),
             ('Dativ nach „mit“?', 'mit seinem aktuellen Lebenslauf.'),
             ('Artikel von „Möglichkeit“?', 'die Möglichkeit.'),
             ('Warum ist „Entscheidung“ feminin?', 'Die Endung -ung ist sehr zuverlässig feminin.'),
             ('Welche B1-Struktur wird im Text verwendet?', 'einerseits … andererseits.')]}]

CSS = '\n:root{\n  --gender-m:#2563eb; --gender-f:#be123c; --gender-n:#15803d;\n  --case-nom:#0f766e; --case-akk:#7c3aed; --case-dat:#d97706;\n  --ink:#1f2937; --muted:#6b7280; --line:#e5e7eb; --paper:#fff; --bg:#f7f8fa;\n}\n*{box-sizing:border-box}\nhtml{scroll-behavior:smooth}\nbody{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.82}\na{color:inherit}\n#top{scroll-margin-top:90px}\n.toolbar{position:sticky;top:0;z-index:20;background:rgba(255,255,255,.96);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}\n.toolbar-inner{max-width:1180px;margin:auto;padding:10px 20px;display:flex;gap:10px 16px;align-items:center;flex-wrap:wrap}\n.toolbar strong{margin-right:4px}\n.toggle{display:inline-flex;align-items:center;gap:6px;font-size:.9rem;white-space:nowrap}\n.mode-buttons{margin-left:auto;display:flex;gap:8px}\n.toolbar-legend{display:flex;flex-wrap:wrap;gap:6px 16px;padding:2px 20px 10px;max-width:1180px;margin:auto;font-size:.8rem;color:var(--muted)}\n.mini-legend{display:inline-flex;align-items:center;gap:5px;white-space:nowrap}\n.mini-legend .case-sample,.mini-legend .gender{font-size:.8rem;padding:0 1px}\nbutton{border:1px solid #d1d5db;background:white;color:var(--ink);border-radius:999px;padding:7px 11px;cursor:pointer}\nbutton:hover{background:#f3f4f6}\n.wrapper{max-width:1180px;margin:0 auto;padding:34px 20px 80px;display:grid;grid-template-columns:260px minmax(0,1fr);gap:28px}\n.sidebar{position:sticky;top:86px;align-self:start;max-height:calc(100vh - 105px);overflow:auto;padding:18px;background:white;border:1px solid var(--line);border-radius:16px}\n.sidebar h3{margin-top:0;font-size:1rem}\n.side-quick{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:10px}\n.sidebar a{display:block;text-decoration:none;padding:7px 8px;border-radius:8px;font-size:.87rem;line-height:1.3}\n.sidebar a:hover{background:#f3f4f6}\n.hero,.story,.index-panel{background:var(--paper);border:1px solid var(--line);border-radius:18px;box-shadow:0 7px 25px rgba(0,0,0,.035)}\n.hero,.index-panel{padding:34px 38px;margin-bottom:26px}\n.hero h1{margin:.1em 0 .4em;font-size:clamp(1.8rem,4vw,2.65rem);line-height:1.12}\n.hero p{max-width:820px}\n.legend{margin-top:24px;padding-top:20px;border-top:1px solid var(--line);display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px 28px}\n.legend-item{font-size:.95rem}\n.case-sample,.case{text-decoration-line:underline;text-decoration-thickness:3px;text-underline-offset:5px;text-decoration-skip-ink:none}\n.case-sample.nom,.case.nom{text-decoration-color:var(--case-nom)}\n.case-sample.akk,.case.akk{text-decoration-color:var(--case-akk)}\n.case-sample.dat,.case.dat{text-decoration-color:var(--case-dat)}\n.gender.m,.article.m{color:var(--gender-m)}\n.gender.f,.article.f{color:var(--gender-f)}\n.gender.n,.article.n{color:var(--gender-n)}\n.gender,.article{font-weight:750}\n.trigger{font-weight:800}\n.trigger.nom{color:var(--case-nom)}\n.trigger.akk{color:var(--case-akk)}\n.trigger.dat{color:var(--case-dat)}\n.ending{font-weight:800;background:none;padding:0}\n.case.nom .ending{color:var(--case-nom)}\n.case.akk .ending{color:var(--case-akk)}\n.case.dat .ending{color:var(--case-dat)}\n.gender.new{border-radius:4px;padding:1px 4px;margin:0 -4px;box-shadow:inset 0 0 0 1px rgba(0,0,0,.05)}\n.gender.new.m{background:rgba(37,99,235,.14)}\n.gender.new.f{background:rgba(190,18,60,.14)}\n.gender.new.n{background:rgba(21,128,61,.14)}\nbody.no-new .gender.new{background:none!important;box-shadow:none!important;padding:0;margin:0}\n.b1{text-decoration-line:underline;text-decoration-style:dotted;text-decoration-color:#6b7280;text-underline-offset:3px}\n.story{padding:30px 34px;margin:0 0 26px;scroll-margin-top:88px}\n.story-head{display:flex;justify-content:space-between;gap:16px;align-items:start}\n.story h2{margin:.15em 0 .8em;font-size:1.65rem;line-height:1.2}\n.eyebrow{color:var(--muted);font-size:.82rem;letter-spacing:.04em;text-transform:uppercase;font-weight:700}\n.toplink{color:var(--muted);font-size:.85rem;text-decoration:none}\n.targets{padding:16px 18px;border:1px solid var(--line);background:#fafafa;border-radius:14px;margin:18px 0 24px}\n.targets h3,.recall h3{margin:0 0 12px;font-size:1rem}\n.noun-grid{display:flex;flex-wrap:wrap;gap:8px}\n.noun-chip{display:inline-flex;align-items:baseline;gap:4px;border:1px solid #e5e7eb;background:white;border-radius:999px;padding:4px 9px;font-size:.87rem}\n.noun-chip[data-en]{position:relative;cursor:pointer;user-select:none}\n.noun-chip[data-en]::after{content:attr(data-en);position:absolute;left:50%;bottom:calc(100% + 8px);transform:translateX(-50%) translateY(4px);min-width:max-content;max-width:220px;padding:6px 9px;border-radius:8px;background:#111827;color:#fff;font-size:.78rem;line-height:1.25;opacity:0;pointer-events:none;transition:opacity .14s ease,transform .14s ease;z-index:30;box-shadow:0 6px 18px rgba(0,0,0,.16)}\n.noun-chip[data-en].show-meaning::after,.noun-chip[data-en]:focus::after,.noun-chip[data-en]:hover::after{opacity:1;transform:translateX(-50%) translateY(0)}\n.noun-chip[data-en]:focus{outline:2px solid #9ca3af;outline-offset:2px}\n.story-text{font-size:1.12rem}\n.story-text p{margin:1.15em 0}\n.bridge{margin-top:24px;padding:12px 15px;background:#fbfbfc;border:1px solid var(--line);border-radius:12px}\n.bridge summary{cursor:pointer;font-weight:700}\n.bridge ul{margin-bottom:0}\n.recall{margin-top:22px;padding-top:20px;border-top:1px solid var(--line)}\n.recall-item{border-top:1px solid #eef0f2;padding:10px 0}\n.recall-item:first-of-type{border-top:0}\n.recall-item summary{cursor:pointer;font-weight:650}\n.answer{margin-top:7px;color:#374151;padding-left:12px;border-left:3px solid #d1d5db}\n.note{padding:12px 14px;background:#f9fafb;border-left:4px solid #9ca3af;border-radius:8px}\n.stats{display:flex;gap:12px;flex-wrap:wrap;margin:18px 0}\n.stat{background:#f9fafb;border:1px solid var(--line);border-radius:12px;padding:10px 14px}\n.stat b{display:block;font-size:1.25rem}\n.index-panel{scroll-margin-top:88px}\n.index-panel h2{margin:.15em 0 .6em;font-size:1.65rem}\n.tablewrap{overflow:auto}\n.course-table{border-collapse:collapse;width:100%;font-size:.91rem}\n.course-table th,.course-table td{padding:10px 11px;border-bottom:1px solid #eceff2;text-align:left;vertical-align:top}\n.course-table th{font-size:.76rem;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}\n.course-table a{text-decoration:none;font-weight:650}\n.alpha-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:7px 18px}\n.alpha-item{font-size:.91rem;border-bottom:1px dotted #e5e7eb;padding:4px 0}\n.b1-grid{columns:3;column-gap:28px}\n.b1-item{break-inside:avoid;padding:3px 0;font-size:.91rem}\n.donecheck{font-size:.78rem;color:var(--muted);white-space:nowrap}\n.donecheck label{margin-right:10px;cursor:pointer}\n.donecheck input{margin-right:4px;vertical-align:middle}\n.story-progress{display:flex;gap:14px;font-size:.85rem;color:var(--muted);margin-top:10px}\n.story-progress label{cursor:pointer;display:inline-flex;align-items:center;gap:4px}\n.progress-summary{font-size:.85rem;color:var(--muted);margin:-6px 0 16px}\n.story-nav{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-top:26px;padding-top:18px;border-top:1px solid var(--line);font-size:.9rem}\n.story-nav-link{text-decoration:none;font-weight:650;color:var(--ink);max-width:38%}\n.story-nav-link:hover{text-decoration:underline}\n.story-nav-mid{color:var(--muted);text-decoration:none;font-size:.82rem;white-space:nowrap}\nbody.no-gender .gender,body.no-gender .article{color:inherit!important;font-weight:inherit!important}\nbody.no-case .case{text-decoration-color:transparent!important}\nbody.no-trigger .trigger{color:inherit!important;font-weight:inherit!important}\nbody.no-ending .ending{font-weight:inherit!important;color:inherit!important}\nbody.no-b1 .b1{text-decoration:none!important}\n@media(max-width:900px){\n  .wrapper{grid-template-columns:1fr}\n  .sidebar{position:relative;top:0;max-height:none}\n  .legend{grid-template-columns:1fr}\n  .mode-buttons{margin-left:0;width:100%}\n  .alpha-grid{grid-template-columns:repeat(2,minmax(0,1fr))}\n  .b1-grid{columns:2}\n}\n@media(max-width:560px){\n  .hero,.story,.index-panel{padding:24px 20px}\n  .alpha-grid{grid-template-columns:1fr}\n  .b1-grid{columns:1}\n}\n@media print{\n  .toolbar,.sidebar,.toplink{display:none!important}\n  .wrapper{display:block;max-width:100%;padding:0}\n  .story,.hero,.index-panel{box-shadow:none}\n}\n'
JS = "\nconst toggles=[\n  ['tg-gender','no-gender'],['tg-case','no-case'],['tg-trigger','no-trigger'],\n  ['tg-ending','no-ending'],['tg-b1','no-b1'],['tg-new','no-new']\n];\nfunction syncClass(id,cls){\n  const el=document.getElementById(id);\n  document.body.classList.toggle(cls,!el.checked);\n}\ntoggles.forEach(([id,cls])=>{\n  document.getElementById(id).addEventListener('change',()=>syncClass(id,cls));\n});\nfunction setChecked(id,val){\n  const el=document.getElementById(id);\n  el.checked=val;\n  el.dispatchEvent(new Event('change'));\n}\nfunction mode(which){\n  if(which==='full'){\n    setChecked('tg-gender',true);setChecked('tg-case',true);setChecked('tg-trigger',true);setChecked('tg-ending',true);setChecked('tg-b1',true);setChecked('tg-new',true);\n  }else if(which==='case'){\n    setChecked('tg-gender',false);setChecked('tg-case',true);setChecked('tg-trigger',true);setChecked('tg-ending',true);setChecked('tg-b1',false);setChecked('tg-new',true);\n  }else{\n    setChecked('tg-gender',false);setChecked('tg-case',false);setChecked('tg-trigger',false);setChecked('tg-ending',false);setChecked('tg-b1',false);setChecked('tg-new',false);\n  }\n}\ndocument.querySelectorAll('.noun-chip[data-en]').forEach(el=>{\n  el.addEventListener('click',(e)=>{\n    e.stopPropagation();\n    document.querySelectorAll('.noun-chip.show-meaning').forEach(x=>{if(x!==el)x.classList.remove('show-meaning')});\n    el.classList.toggle('show-meaning');\n  });\n  el.addEventListener('keydown',(e)=>{\n    if(e.key==='Enter'||e.key===' '){e.preventDefault();el.click();}\n  });\n});\ndocument.addEventListener('click',()=>{\n  document.querySelectorAll('.noun-chip.show-meaning').forEach(x=>x.classList.remove('show-meaning'));\n});\nconst PROGRESS_KEY='german-reader-progress-v1';\nfunction loadProgress(){\n  try{ return JSON.parse(localStorage.getItem(PROGRESS_KEY))||{}; }catch(e){ return {}; }\n}\nfunction saveProgress(data){\n  try{ localStorage.setItem(PROGRESS_KEY,JSON.stringify(data)); }catch(e){}\n}\nfunction progressKey(story,kind){ return story+':'+kind; }\nfunction updateProgressSummary(){\n  const readBoxes=document.querySelectorAll('.donecheck input[data-kind=\"read\"]');\n  const recallBoxes=document.querySelectorAll('.donecheck input[data-kind=\"recall\"]');\n  let read=0,recall=0;\n  readBoxes.forEach(el=>{ if(el.checked) read++; });\n  recallBoxes.forEach(el=>{ if(el.checked) recall++; });\n  const el=document.getElementById('progress-summary');\n  if(el) el.textContent='Read: '+read+'/'+readBoxes.length+'  ·  Recall checked: '+recall+'/'+recallBoxes.length;\n}\nfunction initProgress(){\n  const data=loadProgress();\n  document.querySelectorAll('.progress-check').forEach(el=>{\n    const key=progressKey(el.dataset.story,el.dataset.kind);\n    el.checked=!!data[key];\n  });\n  document.querySelectorAll('.progress-check').forEach(el=>{\n    el.addEventListener('change',()=>{\n      const d=loadProgress();\n      const key=progressKey(el.dataset.story,el.dataset.kind);\n      d[key]=el.checked;\n      saveProgress(d);\n      document.querySelectorAll('.progress-check[data-story=\"'+el.dataset.story+'\"][data-kind=\"'+el.dataset.kind+'\"]').forEach(other=>{ other.checked=el.checked; });\n      updateProgressSummary();\n    });\n  });\n  updateProgressSummary();\n}\ninitProgress();\n"


# Maps each target noun (casefolded) to the number of the story that first
# introduces it, so paragraph rendering can highlight first-time appearances.
NOUN_HOME: dict = {}
for _story in STORIES:
    for _gender, _noun, _english in _story["targets"]:
        NOUN_HOME.setdefault(_noun.strip().casefold(), _story["number"])


def bold_endings(text: str) -> str:
    """Convert [ending] to the visual ending span."""
    return re.sub(r"\[([^\]]+)\]", r'<strong class="ending">\1</strong>', text)


def gender_span(gender: str, noun: str, story_number: int) -> str:
    """Render a gender-colored noun span, flagging first-time appearances."""
    is_new = NOUN_HOME.get(noun.strip().casefold()) == story_number
    cls = f"gender {gender} new" if is_new else f"gender {gender}"
    return f'<span class="{cls}">{noun}</span>'


def parse_markup(text: str, story_number: int) -> str:
    """Render the lightweight linguistic markup inside one story paragraph."""
    # B1 bridge: ((word|gloss))
    text = re.sub(
        r"\(\(([^|()]+)\|([^()]+)\)\)",
        lambda m: f'<span class="b1" title="{html.escape(m.group(2), quote=True)}">{m.group(1)}</span>',
        text,
    )

    # Trigger: [[akk|sehen]]
    text = re.sub(
        r"\[\[(nom|akk|dat)\|([^\]]+)\]\]",
        lambda m: f'<span class="trigger {m.group(1)}">{m.group(2)}</span>',
        text,
    )

    # Case phrase: {akk|m|d[en] alt[en]|Mann}
    def case_repl(m):
        case_name, gender, left, noun = m.group(1), m.group(2), m.group(3), m.group(4)
        left = bold_endings(left.strip())
        spacer = " " if left else ""
        return (
            f'<span class="case {case_name}">{left}{spacer}'
            f'{gender_span(gender, noun, story_number)}</span>'
        )
    text = re.sub(
        r"\{\{(nom|akk|dat)\|(m|f|n)\|([^|{}]*)\|([^{}]+)\}\}",
        case_repl,
        text,
    )

    # Gender-only noun: <<m|Tisch>>
    text = re.sub(
        r"<<(m|f|n)\|([^<>]+)>>",
        lambda m: gender_span(m.group(1), m.group(2), story_number),
        text,
    )
    return text.replace("\n", "<br>")


def validate_course() -> None:
    """Fail early when source data becomes inconsistent."""
    expected = list(range(1, len(STORIES) + 1))
    actual = [s["number"] for s in STORIES]
    if actual != expected:
        raise ValueError(f"Story numbers must be sequential: expected {expected}, got {actual}")

    seen = set()
    for story in STORIES:
        if not story["paragraphs"]:
            raise ValueError(f'Story {story["number"]} has no paragraphs')
        if not story["targets"]:
            raise ValueError(f'Story {story["number"]} has no target nouns')
        for g, noun, english in story["targets"]:
            if g not in ARTICLES:
                raise ValueError(f'Invalid gender {g!r} for {noun}')
            if not english.strip():
                raise ValueError(f'Missing English meaning for {noun}')
            key = noun.casefold()
            if key in seen:
                raise ValueError(f'Duplicate target noun: {noun}')
            seen.add(key)


def render_target_chip(g: str, noun: str, english: str) -> str:
    art = ARTICLES[g]
    label = html.escape(f"{art} {noun}: {english}", quote=True)
    gloss = html.escape(english, quote=True)
    return (
        f'<span class="noun-chip" data-en="{gloss}" tabindex="0" role="button" aria-label="{label}">'
        f'<span class="article {g}">{art}</span> '
        f'<span class="gender {g}">{html.escape(noun)}</span></span>'
    )


def render_story(story: dict, prev_story: dict = None, next_story: dict = None) -> str:
    n = story["number"]
    targets = "\n".join(render_target_chip(*x) for x in story["targets"])
    paragraphs = "\n".join(f"<p>{parse_markup(p, n)}</p>" for p in story["paragraphs"])
    b1_items = "".join(f"<li>{html.escape(x)}</li>" for x in story["b1"])
    recalls = []
    for idx, (q, a) in enumerate(story["recall"], 1):
        recalls.append(
            f'<details class="recall-item"><summary>{idx}. {html.escape(q)}</summary>'
            f'<div class="answer">{html.escape(a)}</div></details>'
        )
    if prev_story:
        prev_link = f'<a class="story-nav-link prev" href="#story-{prev_story["number"]}">← {html.escape(prev_story["title"])}</a>'
    else:
        prev_link = '<span></span>'
    if next_story:
        next_link = f'<a class="story-nav-link next" href="#story-{next_story["number"]}">{html.escape(next_story["title"])} →</a>'
    else:
        next_link = '<span></span>'
    return f"""
<section class="story" id="story-{n}">
  <div class="story-head">
    <div>
      <div class="eyebrow">Story {n} · A2 core + light B1</div>
      <h2>{html.escape(story["title"])}</h2>
    </div>
    <a class="toplink" href="#top">↑ top</a>
  </div>

  <div class="story-progress">
    <label><input type="checkbox" class="progress-check" data-story="{n}" data-kind="read"> Mark as read</label>
    <label><input type="checkbox" class="progress-check" data-story="{n}" data-kind="recall"> Recall done</label>
  </div>

  <div class="targets">
    <h3>{len(story["targets"])} target nouns · tap/hover for English</h3>
    <div class="noun-grid">{targets}</div>
  </div>

  <div class="story-text">
    {paragraphs}
  </div>

  <details class="bridge">
    <summary>B1 bridge words in this story</summary>
    <ul>{b1_items}</ul>
  </details>

  <div class="recall">
    <h3>Recall</h3>
    {''.join(recalls)}
  </div>

  <div class="story-nav">
    {prev_link}
    <a class="story-nav-mid" href="#course-index">Course map</a>
    {next_link}
  </div>
</section>
"""


def render_course_index() -> str:
    rows = []
    for s in STORIES:
        n = s["number"]
        rows.append(
            f'<tr><td>{n}</td>'
            f'<td><a href="#story-{n}">{html.escape(s["title"])}</a></td>'
            f'<td>{len(s["targets"])}</td><td>{len(s["b1"])}</td>'
            f'<td class="donecheck">'
            f'<label><input type="checkbox" class="progress-check" data-story="{n}" data-kind="read"> read</label>'
            f'<label><input type="checkbox" class="progress-check" data-story="{n}" data-kind="recall"> recall</label>'
            f'</td></tr>'
        )
    return f"""
<section class="index-panel" id="course-index">
  <div class="eyebrow">Navigation</div>
  <h2>Course map</h2>
  <div class="progress-summary" id="progress-summary"></div>
  <div class="tablewrap">
    <table class="course-table">
      <thead><tr><th>#</th><th>Story</th><th>Target nouns</th><th>B1 bridge</th><th>Progress</th></tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
  </div>
</section>
"""


def render_noun_index() -> str:
    items = []
    for s in STORIES:
        for g, noun, english in s["targets"]:
            items.append((noun.casefold(), noun, g, english, s["number"]))
    items.sort()
    parts = []
    for _, noun, g, english, story_no in items:
        parts.append(
            f'<div class="alpha-item"><a href="#story-{story_no}">'
            f'<span class="article {g}">{ARTICLES[g]}</span> '
            f'<span class="gender {g}">{html.escape(noun)}</span></a>'
            f' — {html.escape(english)}</div>'
        )
    return f"""
<section class="index-panel" id="noun-index">
  <div class="eyebrow">500 high-repetition nouns</div>
  <h2>Alphabetical noun index</h2>
  <div class="alpha-grid">{''.join(parts)}</div>
</section>
"""


def render_b1_index() -> str:
    items = []
    for s in STORIES:
        for word in s["b1"]:
            items.append((word.casefold(), word, s["number"]))
    items.sort()
    body = "".join(
        f'<div class="b1-item"><a href="#story-{story_no}">{html.escape(word)}</a></div>'
        for _, word, story_no in items
    )
    return f"""
<section class="index-panel" id="b1-index">
  <div class="eyebrow">Gentle bridge</div>
  <h2>B1 bridge index · {len(items)} items</h2>
  <div class="b1-grid">{body}</div>
</section>
"""


def render_sidebar() -> str:
    story_links = "".join(
        f'<a href="#story-{s["number"]}">{s["number"]}. {html.escape(s["title"])}</a>'
        for s in STORIES
    )
    return f"""
<aside class="sidebar">
  <h3>Reader index</h3>
  <div class="side-quick">
    <a href="#course-index">Course map</a>
    <a href="#story-1">Stories</a>
    <a href="#noun-index">Noun index</a>
    <a href="#b1-index">B1 bridge index</a>
    <a href="#grammar-key">Grammar key</a>
  </div>
  {story_links}
</aside>
"""


def render_hero() -> str:
    noun_total = sum(len(s["targets"]) for s in STORIES)
    return f"""
<section class="hero">
  <div class="eyebrow">German graded reader · A2 core with a gentle B1 bridge</div>
  <h1>Cases, gender and vocabulary through connected stories</h1>
  <p>
    The reader keeps <strong>{noun_total} target nouns</strong> as the high-repetition layer for
    gender and case, while the surrounding prose broadens into common A2 verbs, adjectives,
    adverbs and everyday expressions. A small B1 bridge is introduced gradually.
  </p>

  <div class="stats">
    <div class="stat"><b>{len(STORIES)}</b>connected stories</div>
    <div class="stat"><b>{noun_total}</b>high-repetition nouns</div>
    <div class="stat"><b>≈1,200</b>A2-level vocabulary target</div>
    <div class="stat"><b>+120</b>B1 bridge items</div>
  </div>

  <div class="legend" id="grammar-key">
    <div class="legend-item"><span class="gender m">Masculine noun</span> → blue text</div>
    <div class="legend-item"><span class="gender f">Feminine noun</span> → rose/red text</div>
    <div class="legend-item"><span class="gender n">Neuter noun</span> → green text</div>
    <div class="legend-item"><span class="case-sample nom">Nominative phrase</span> → teal underline</div>
    <div class="legend-item"><span class="case-sample akk">Accusative phrase</span> → purple underline</div>
    <div class="legend-item"><span class="case-sample dat">Dative phrase</span> → orange underline</div>
    <div class="legend-item"><span class="trigger akk">sehen</span> → purple trigger = accusative expected</div>
    <div class="legend-item"><span class="trigger dat">mit</span> → orange trigger = dative expected</div>
    <div class="legend-item"><span class="gender m new">Tisch</span> → highlighted = new noun in this story</div>
  </div>

  <p class="note">
    <strong>Visual rule:</strong> noun text color = inherent gender; underline = current case;
    trigger text = what causes/announces that case; every annotated ending is
    <strong>bold and colored with its case</strong>; a soft highlight marks a noun's first
    appearance in the course, so plain gender/case color without the highlight means it's a
    repeat from an earlier story. All paragraphs inside a story use the same system.
  </p>

  <p class="note">
    <strong>Vocabulary:</strong> tap or hover over a target noun to reveal its English meaning.
    B1 bridge expressions use a dotted underline.
  </p>

  <p>
    Recommended use: first read with <strong>Full support</strong>, then reread with
    <strong>Case only</strong>, then use <strong>Plain reading</strong> and predict the forms yourself.
  </p>
</section>
"""


def render_three_pass() -> str:
    return """
<section class="index-panel">
  <div class="eyebrow">Method</div>
  <h2>Three-pass reading</h2>
  <p><strong>Pass 1 — Notice:</strong> read with all visual support enabled.</p>
  <p><strong>Pass 2 — Retrieve:</strong> hide gender colors but keep case underlines, triggers and endings.</p>
  <p><strong>Pass 3 — Read:</strong> switch to plain reading and predict article/adjective forms before you reach them.</p>
</section>
"""


def render_page() -> str:
    validate_course()
    stories_html = "\n".join(
        render_story(
            s,
            STORIES[i - 1] if i > 0 else None,
            STORIES[i + 1] if i + 1 < len(STORIES) else None,
        )
        for i, s in enumerate(STORIES)
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>German A2 → B1 Case + Gender Story Reader</title>
<style>{CSS}</style>
</head>
<body id="top">
<div class="toolbar">
  <div class="toolbar-inner">
    <strong>Display:</strong>
    <label class="toggle"><input id="tg-gender" type="checkbox" checked> Gender colors</label>
    <label class="toggle"><input id="tg-case" type="checkbox" checked> Case underlines</label>
    <label class="toggle"><input id="tg-trigger" type="checkbox" checked> Trigger colors</label>
    <label class="toggle"><input id="tg-ending" type="checkbox" checked> Ending cues</label>
    <label class="toggle"><input id="tg-b1" type="checkbox" checked> B1 hints</label>
    <label class="toggle"><input id="tg-new" type="checkbox" checked> New-word highlight</label>
    <div class="mode-buttons">
      <button onclick="mode('full')">Full support</button>
      <button onclick="mode('case')">Case only</button>
      <button onclick="mode('plain')">Plain reading</button>
    </div>
  </div>
  <div class="toolbar-legend">
    <span class="mini-legend"><span class="gender m">der</span> masc.</span>
    <span class="mini-legend"><span class="gender f">die</span> fem.</span>
    <span class="mini-legend"><span class="gender n">das</span> neut.</span>
    <span class="mini-legend"><span class="case-sample nom">nom</span></span>
    <span class="mini-legend"><span class="case-sample akk">akk</span></span>
    <span class="mini-legend"><span class="case-sample dat">dat</span></span>
    <span class="mini-legend"><span class="gender m new">new</span> = new this story</span>
  </div>
</div>

<div class="wrapper">
  {render_sidebar()}
  <main>
    {render_hero()}
    {render_course_index()}
    {stories_html}
    {render_noun_index()}
    {render_b1_index()}
    {render_three_pass()}
  </main>
</div>

<script>{JS}</script>
</body>
</html>"""


def main() -> None:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("german_a2_b1_case_gender_reader.html")
    output.write_text(render_page(), encoding="utf-8")
    noun_total = sum(len(s["targets"]) for s in STORIES)
    print(f"Created {output.resolve()}")
    print(f"Stories: {len(STORIES)}")
    print(f"Target nouns: {noun_total}")
    print(f"B1 bridge entries: {sum(len(s['b1']) for s in STORIES)}")


if __name__ == "__main__":
    main()
