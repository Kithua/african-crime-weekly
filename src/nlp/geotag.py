import spacy, re
nlp = spacy.load("xx_ent_wiki_sm")
AFRICA = {"Algeria","Angola","Benin","Botswana","Burkina Faso","Burundi","Cameroon","Cape Verde",
          "Central African Republic","Chad","Comoros","Congo","Democratic Republic of the Congo",
          "Djibouti","Egypt","Equatorial Guinea","Eritrea","Eswatini","Ethiopia","Gabon","Gambia",
          "Ghana","Guinea","Guinea-Bissau","Ivory Coast","Kenya","Lesotho","Liberia","Libya",
          "Madagascar","Malawi","Mali","Mauritania","Mauritius","Morocco","Mozambique","Namibia",
          "Niger","Nigeria","Rwanda","São Tomé and Príncipe","Senegal","Seychelles","Sierra Leone",
          "Somalia","South Africa","South Sudan","Sudan","Tanzania","Togo","Tunisia","Uganda",
          "Zambia","Zimbabwe"}
def keep_africa(items):
    out=[]
    for it in items:
        txt = (it.get("title","")+" "+it.get("summary","")).lower()
        if any(c.lower() in txt for c in AFRICA):
            out.append(it)
    return out
