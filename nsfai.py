# Code for scraping https://aiinstitutes.org/institutes/

AIURL = 'https://aiinstitutes.org/institutes/'

import requests
from bs4 import BeautifulSoup

institutes = {}
awardees = {}

canonicalize = { 
    'Georgia Institute of Technology (Georgia Tech)': 'Georgia Institute of Technology',
    'Georgia Tech': 'Georgia Institute of Technology',
    'University of Texas at Austin': 'University of Texas Austin',
    'Multi-campus UC Berkeley Award': 'University of California Berkeley',
    'University of Wisconsin': 'University of Wisconsin-Madison',
    'IBM Research': 'IBM',
    'The University of Washington': 'University of Washington',
    'The Pennsylvania State University': 'Pennsylvania State University',
    'Pennsylvania State University (Penn State)': 'Pennsylvania State University',
    'Texas A&M University-Corpus Christi': 'Texas A&M',
    'University of Illinois Chicago (UIC)': 'University of Illinois at Chicago (UIC)',
    'University of Illinois Urbana-Champaign (UIUC)': 'University of Illinois Urbana-Champaign (UIUC)',
    'University of Illinois at Urbana Champaign (UIUC)': 'University of Illinois Urbana-Champaign (UIUC)',
    'University of Illinois Urbana-Champaign (UIUC)': 'University of Illinois Urbana-Champaign (UIUC)',
    'University of Illinois at Urbana-Champaign (UIUC)': 'University of Illinois Urbana-Champaign (UIUC)',
} 

def countPrimary(awards):
    return sum([1 if award[1] else 0 for award in awards])

def countSub(awards):
    return sum([0 if award[1] else 1 for award in awards])

def updateAwardee(awardee, institute, primary=False):
    if awardee in canonicalize:
        awardee = canonicalize[awardee]

    if awardee in awardees:
        awardees[awardee] += [(institute, primary)]
    else:
        print("New awardee: " + awardee + " (" + institute + ")")
        awardees[awardee] = list([(institute, primary)])

# Making a GET request
r = requests.get(AIURL, headers={"User-Agent": "XY"})

assert r.status_code == 200

# print content of request
# print(r.content)

soup = BeautifulSoup(r.content, 'html.parser')

# what a kludge...but it works for now
s = soup.find('div', class_='elementor-element-b459a52')
# print(s.prettify)

institutes = s.find_all('div', class_='institute-card')
print("Found institutes: " + str(len(institutes)))

links = [institute.find('div', class_='elementor-widget-container').find('a')['href'] 
         for institute in institutes]

for link in links: # [:3]:
    print("Visiting: " + link)
    instpage = requests.get(link, headers={"User-Agent": "XY"})
    assert instpage.status_code == 200
    spage = BeautifulSoup(instpage.content, 'html.parser')
    instname = spage.find('h2').text
    print("Institute: " + instname)

    # search for 'Primary Awardee'
    pars = spage.find_all('p')
    for p in pars:
        if p.text.startswith('Primary Awardee'):
            pli = p.find_next('li')
            if pli:
                # print("Awardee: " + pli.text)
                awardee = pli.text.strip()
                updateAwardee(awardee, instname, primary=True)
            else:
                print("No Item Found")
        if p.text.startswith('Subawardees'):
            sublist = p.find_next('ul')
            subs = sublist.find_all ('li')
            for sub in subs:
                # print ("   Subawardee: " + sub.text)
                awardee = sub.text.strip()
                updateAwardee(awardee, instname, primary=False)

institutions = list(awardees.keys())
institutions.sort()
institutions.sort(key=lambda a: countSub(awardees[a]), reverse=True)
institutions.sort(key=lambda a: countPrimary(awardees[a]), reverse=True)
print("Number of institutions: %d" % (len(institutions)))

fname = 'aiinstitutes.csv'
tname = 'aiinstitute.tex'
with open(tname, 'w') as table:
    with open(fname, 'w') as file:
        file.write("Awardee, Institute, Primary\n")
        table.write("Institution & Primary & Subawardee \\\\\n")
        for awardee in institutions:
            awards = awardees[awardee]
            numprimary = 0
            numsub = 0
            for award in awards:
                file.write("%s, %s, %s\n" % (awardee, award[0], award[1]))
                if award[1]:
                    numprimary += 1
                else:
                    numsub += 1
            assert numprimary + numsub == len(awards)
            print("%s: Primary: %d / Sub: %d" % (awardee, numprimary, numsub))
            table.write("%s & %s & %s \\\\\n" % (awardee, numprimary, numsub))
            for award in awards:
                print ("   %s \t%s" % (award[0], "Primary" if award[1] else "Sub"))
