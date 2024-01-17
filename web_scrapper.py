#web_scrapping.py
import requests
from bs4 import BeautifulSoup


def backmarket(search,page):
    
    backmarket_info=[] # backmarket_info = [[nom_produit,lien,image,garantie,nb_étoile,prix],...]
    sock=requests.get(f"https://www.backmarket.fr/fr-fr/search?q={search}&page={page}")
    if sock.status_code==200:
        
        soup=BeautifulSoup(sock.text, 'html.parser')
        produits=soup.find_all(class_='productCard')
        
        if produits==[]:
            return ([],0)
        
        nb_pages=soup.find_all('a',class_="inline-flex")
        
        if nb_pages!=[]:
            nb_pages=int(nb_pages[len(nb_pages)-1].text.strip())
        else:
            nb_pages=1
        
        for elt in produits:
    
            info_img=elt.find('img')

            #cherche nom du produit
    
            nom=info_img['alt']

            #cherche le lien

            lien=elt.find('a',href=True)['href']
            lien='https://www.backmarket.fr'+lien
        
            #cherche l'image du produit

            img='http'+info_img['src'].split('http')[1]
    
            #cherche la garantie

            garantie=elt.find(class_="body-2-light text-black").text.strip().split(':')[1]
    
            #cherche le nb d'étoile

            nb_étoiles=len(elt.find_all(lambda tag: tag.name == 'svg' and 'aria-label' in tag.attrs and tag['aria-label'] == 'filledStar'))
            nb_étoiles+=len(elt.find_all(lambda tag: tag.name == 'svg' and 'aria-label' in tag.attrs and tag['aria-label'] == 'halfFilledStar'))*0.5
            if nb_étoiles==0:
                nb_étoiles=-1
            #cherche le prix
        
            #prix_entier_et_centime=elt.find(class_='body-2-bold text-black').text.replace(' ','').strip().split('€')[0].replace('\xa0','').replace('\u202f','').split(',')            
            #prix=int(prix_entier_et_centime[0])+int(prix_entier_et_centime[1])/100
            prix=elt.find(class_='body-2-bold text-black').text
                        
            backmarket_info.append([nom,lien,img,garantie,str(nb_étoiles),str(prix)])
    else:
        return ([],0)   
    return(backmarket_info,nb_pages)


def afbshop(search,page):
    
    afbshop_info=[] #afbshop_info = [nom_produit,lien,image,état,prix]
    sock=requests.get(f'https://www.afbshop.fr/search?order=score&p={page}&search={search}')
    if sock.status_code==200:

        soup=BeautifulSoup(sock.text, 'html.parser')
        produits=soup.find_all('div', class_='card-body row')
        
        if produits==[]:
            return ([],0)
        
        nb_pages=soup.find(id='p-last')
        
        if nb_pages!=None:
            nb_pages=int(nb_pages['value'])
        else:
            nb_pages=1
        
        for elt in produits:

            produits_infos=elt.find('a',class_='product-name')
            nom=produits_infos['title']
            
            lien=produits_infos['href']

            image=elt.find('img',class_='product-image is-standard')['src']

            état=elt.find('div', class_='product-variant-characteristics-option product-variant-characteristics-option-active')
            if état!=None:
                état=état.text.strip()

            prix_entier_et_centime=elt.find('span', class_='product-price').text.replace(' ','').strip().split('€')[0].replace('\xa0','').replace('\u202f','').split(',')            
            prix=str(int(prix_entier_et_centime[0])+int(prix_entier_et_centime[1])/100)
           
            afbshop_info.append([nom,lien,image,état,prix])
    else:
        return([],0)   
    
    return(afbshop_info,nb_pages)

def ebay(search,page):
    
    ebay_infos=[] # ebay_infos = [nom_produit,lien,image,état,détails]  !!état et détails sont des listes!!
    url=f'https://www.ebay.fr/sch/i.html?_nkw={search}&_pgn={page}'
    sock=requests.get(url)
    if sock.status_code==200:
        soup=BeautifulSoup(sock.text,'html.parser')
        produits=soup.find_all('li',class_='s-item s-item__pl-on-bottom')
        
        if produits==[]:
            return ([],0)
        produits.remove(produits[0])
        if produits==[]:
            return ([],0)
        nb_pages=soup.find_all('a',class_='pagination__item')
        if nb_pages!=[]:
            nb_pages=int(nb_pages[-1].text)
        else:
            nb_pages=1

        for elt in produits:

            infos_produit=elt.find('a',class_='s-item__link')

            nom_produit=infos_produit.text

            lien=infos_produit['href']

            image=elt.find('img')['src']

            état=elt.find_all('div',class_='s-item__subtitle')
            for i in range(len(état)):
                état[i]=état[i].text
            
            détails=elt.find('div', class_='s-item__details clearfix').find_all('div', class_='s-item__detail s-item__detail--primary')
            for i in range(len(détails)):
                if détails[i].text!=' Sponsorisé':
                    détails[i]=détails[i].text
                else:
                    détails.remove(détails[i])
            
            ebay_infos.append([nom_produit,lien,image,état,détails])
    else:
        return ([],0)
    
    return (ebay_infos,nb_pages)




