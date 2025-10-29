#!/usr/bin/env python3
"""
Deduplicate & 404-filter a block of URLs and append them
to an existing whitelist yaml file used by African-Crime-Weekly.
"""

import sys, os, yaml, requests, itertools
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

SRC_YAML = "whitelist_multilingual.yml"   # existing file in repo root
TIMEOUT  = 10
MAX_REDIRECTS = 5
WORKERS = 32

# ---------- raw block you pasted (keep the triple quotes) ----------
RAW_HTTPS = """
https://www.jornaldeangola.ao/ao/
https://jornalf8.net/
https://novojornal.co.ao/
https://opais.co.ao/
https://correiokianda.info/
https://www.makaangola.org/en/
https://angola24horas.com/
https://platinaline.com/
https://www.portaldeangola.com/
https://www.expansao.co.ao/
https://www.verangola.net/va/
https://www.angonoticias.com/
https://www.w3newspapers.com/portugal/
https://angola-online.net/
https://www.novagazeta.co.ao/
https://www.vozdeangola.com/
https://noticiasdeangola.co.ao/

https://www.echoroukonline.com/
https://www.echoroukonline.com/
https://www.elkhabar.com/
https://www.elkhabar.com/
https://www.el-massa.com/
https://www.el-massa.com/
http://www.ech-chaab.com/
http://www.ech-chaab.com/
https://www.ennaharonline.com/
https://www.ennaharonline.com/
https://akhersaa.net/
https://akhersaa.net/
https://www.annasronline.com/
https://www.eldjoumhouria.dz/
https://www.akhbarelyoum.dz/ar/index.php
https://www.alseyassi-dz.com/ara/index.php
https://elwassat.dz/
https://elhayat.dz/
https://www.lexpressiondz.com/
https://www.lexpressiondz.com/
https://elwatan-dz.com/
https://www.elmoudjahid.com/
https://www.lequotidien-oran.com/
https://www.lesoirdalgerie.com/
https://www.lejourdalgerie.com/
https://www.depechedekabylie.com/
https://www.reflexiondz.net/
http://www.alger-republicain.com/
https://www.horizons.dz/
https://lecourrier-dalgerie.com/
https://lecarrefourdalgerie.dz/
https://lechodalgerie.dz/
https://www.jeune-independant.net/
https://transactiondalgerie.com/
https://algerie-eco.com/
https://algeriemaintenant.com/
http://lautomarche.com/
https://north-africa.com/
https://www.elheddaf.com/
https://www.elheddaf.com/
https://www.dzfoot.com/
https://www.lebuteur.com/
https://www.competition.dz/
https://algerie.football/
https://www.lematindz.net/
https://www.lematindz.net/
https://www.elbilad.net/
https://www.algerie360.com/
https://www.algerie1.com/
https://algeriepatriotique.com/
https://dzayerinfo.com/
https://www.aljazairalyoum.dz/
https://lematindalgerie.com/
https://www.algerie-focus.com/
https://elhiwar.dz/
https://dia-algerie.com/
https://www.algerie-dz.com/
https://djelfainfo.dz/ar/
https://al24news.dz/
https://www.aps.dz/
https://news.radioalgerie.dz/
https://www.entv.dz/
https://observalgerie.com/
https://www.w3newspapers.com/france/
https://dnalgerie.com/
https://www.diasporadz.com/
https://www.francemaghreb2.fr/
https://www.beurfm.net/
https://www.canadalgerie.info/
https://www.w3newspapers.com/canada/
https://ar.w3newspapers.com/%D8%A7%D9%84%D8%AC%D8%B2%D8%A7%D8%A6%D8%B1/
https://www.w3newspapers.com/egypt/
https://www.w3newspapers.com/morocco/
https://www.w3newspapers.com/nigeria/
https://www.w3newspapers.com/algeria/
https://www.w3newspapers.com/algeria/#top
https://www.facebook.com/sharer.php?u=https://www.w3newspapers.com/algeria/
https://x.com/share?url=https://www.w3newspapers.com/algeria/

https://novojornal.co.ao/ 
https://www.verangola.net/va/en
https://www.topafricanews.com/
https://kewoulo.info/cat%C3%A9gories/politique/
https://www.echoroukonline.com/
https://www.elkhabar.com/
https://www.el-massa.com/
http://www.ech-chaab.com/
https://www.ennaharonline.com/
https://akhersaa.net/
https://www.lexpressiondz.com/
https://elwatan-dz.com/
https://www.elmoudjahid.com/
https://www.jornaldeangola.ao/ao/ 

https://lanation.bj/
https://lanouvelletribune.info/
http://www.quotidienlematin.net/
https://levenementprecis.com/
https://www.24haubenin.info/
http://www.acotonou.com/
https://visages-du-benin.com/
http://beninsite.net/
http://www.l-integration.com/
https://matinlibre.com/
https://benininfo.com/
https://fraternitebj.info/
https://www.bbc.com/news/world-africa-13037572
https://www.gouv.bj/

https://guardiansun.co.bw/
https://www.mmegi.bw/
https://thevoicebw.com/
https://dailynews.gov.bw/
https://thepatriot.co.bw/
https://www.sundaystandard.info/
https://www.weekendpost.co.bw/
https://botswanaunplugged.com/
https://kutlwano.gov.bw/
https://www.facebook.com/botsmag/
https://allafrica.com/botswana/
https://guardiansun.co.bw/business
http://www.bnsc.co.bw/

https://www.lobservateur.bf/
https://lepays.bf/
https://www.w3newspapers.com/france/
https://www.sidwaya.info/
https://lefaso.net/
https://burkina24.com/
https://www.leconomistedufaso.com/
https://faso-actu.net/
https://www.aujourd8.net/
https://www.lexpressdufaso-bf.com/
https://lesaffairesbf.com/
https://www.evenement-bf.net/
https://www.rtb.bf/
http://www.fasozine.com/
https://www.fasopresse.net/
https://www.reporterbf.net/
https://burkinainfo.com/
https://www.aib.media/
http://www.aouaga.com/
https://allafrica.com/burkinafaso/

https://www.iwacu-burundi.org/
https://isanganiro.org/
https://www.netpress.online/
https://burundi-agnews.org/
https://www.yaga-burundi.com/
http://www.arib.info/
https://burundi-forum.org/
https://www.burundi-information.net/index.html
https://burundi24.wordpress.com/
https://itaraburundi.com/
https://allafrica.com/burundi/
https://www.jeuneafrique.com/pays/burundi/

https://fr.journalducameroun.com/
https://www.cameroon-info.net/
https://camer.be/
https://www.lebledparle.com/
https://actucameroun.com/
https://www.camfoot.com/
https://crtv.cm/
https://237actu.com/
https://www.237online.com/
http://www.canal2international.net/
https://agencepressecamertest.com/
https://cameroonvoice.com/
https://www.cameroun24.net/
https://www.cameroononline.org/
https://www.lavoixdupaysan.net/
https://www.bonaberi.com/
https://lequatriemepouvoir.com/
https://www.newsducamer.com/
https://www.cameroonbusinesstoday.cm/
https://yaoundeinfo.com/
https://solowayne.com/
https://cameroonnewsagency.com/
https://www.cameroonconcordnews.com/
https://camerounlink.com/
https://germinalnewspaper.com/
https://www.cameroonnewsline.com/
https://www.lattaquant.com/

https://asemana.cv/
https://www.w3newspapers.com/portugal/
https://expressodasilhas.cv/
https://www.anacao.cv/
https://inforpress.cv/
https://www.rtc.cv/
https://terranova.cv/
https://www.criolosports.com/
https://noticiasdonorte.publ.cv/
https://www.brava.news/en
http://sportsmidia.cv/
http://www.fogo.cv/
https://www.jeuneafrique.com/pays/cap-vert/

https://www.centrafrique-presse.info/
http://www.sangonet.com/afriqg/PAFF/Dic/actuC/newsCARind.html
https://www.journaldebangui.com/
https://www.radiondekeluka.org/
https://www.centrafriqueledefi.com/
http://www.centrafrique.info/
https://www.jeuneafrique.com/pays/centrafrique/
https://allafrica.com/centralafricanrepublic/

https://www.alwihdainfo.com/
https://journaldutchad.com/
https://tchadinfos.com/
https://www.letchadanthropus-tribune.com/
http://www.lepaystchad.com/
https://zoomtchad.com/
https://reliefweb.int/country/tcd
https://www.jeuneafrique.com/pays/tchad/

https://www.alwatwan.net/
https://www.habarizacomores.com/
http://lemohelien.com/
https://lagazettedescomores.com/

https://actualite.cd/
https://acpcongo.com/
https://deskeco.com/
https://laprosperiteonline.net/
https://www.radiookapi.net/
https://www.forumdesas.org/
https://footrdc.com/
https://congosynthese.com/
https://lephareonline.net/
http://voiceofcongo.net/
https://cas-info.ca/
https://www.mediacongo.net/
https://congoprofond.net/
http://www.congoindependant.com/
https://www.congoplanet.com/
https://www.lesoftonline.net/

https://www.lanation.dj/
https://laprosperiteonline.net/
https://lavoixdedjibouti.info/
https://www.alqarn.dj/
http://www.adi.dj/
https://reliefweb.int/country/dji

https://gate.ahram.org.eg/
https://gate.ahram.org.eg/
https://akhbarelyom.com/
https://akhbarelyom.com/
https://www.almasryalyoum.com/
https://www.almasryalyoum.com/
https://www.dostor.org/
https://www.dostor.org/
https://www.youm7.com/
https://www.youm7.com/
https://www.albawabhnews.com/
https://www.albawabhnews.com/
https://www.alwafd.news/
https://www.alwafd.news/
https://www.vetogate.com/
https://www.vetogate.com/
https://www.elwatannews.com/
https://www.elwatannews.com/
https://www.elfagr.org/
https://www.elfagr.org/
https://www.gomhuriaonline.com/
https://www.gomhuriaonline.com/
https://www.w3newspapers.com/arabic/
https://www.shorouknews.com/
https://www.shorouknews.com/
https://english.ahram.org.eg/
https://www.elmogaz.com/
https://ahlmasrnews.com/
https://www.filgoal.com/
https://arabi21.com/
https://www.elzmannews.com/
https://www.elbalad.news/
https://www.dotmsr.com/
https://www.ngmisr.com/
https://www.arabnet5.com/
https://rassd.com/
https://www.darelhilal.com/
https://www.masrawy.com/
https://propaganda-eg.com/
https://www.masress.com/
http://www.almogaz.com/
https://sharkiatoday.com/
https://www.wataninet.com/
http://www.washwasha.org/
https://tv.koorabia.com/
https://www.masralyoum.net/
https://akhbarak.net/
https://www.alaraby.co.uk/
https://www.almasdar.com/
https://www.sabaharabi.com/
https://www.mobtada.com/
https://almesryoon.com/
https://fj-p.com/
https://misr5.com/
https://www.akhbarway.com/
https://gate.ahram.org.eg/
https://almalnews.com/
https://www.alnaharegypt.com/
https://www.kooora.com/
https://www.el-ahly.com/
https://www.ismailyonline.com/
https://stadelahly.net/
https://elbashayer.com/
https://www.maspero.eg/
https://www.niletc.tv/
https://www.ikhwanonline.com/
https://arabmix.news/
https://www.alwatanpost.net/
https://www.elaosboa.com/
https://www.qaliubiya.com/
https://alahalygate.com/
http://www.soutalmalaien.com/
https://fath-news.com/
https://amwalalghad.com/
https://www.soutalomma.com/
https://www.madamasr.com/
https://egyptianstreets.com/
https://www.mogazmasr.com/
https://www.egypt-today.com/
https://www.w3newspapers.com/uk/
https://www.sis.gov.eg/
https://www.dailynewsegypt.com/
https://www.egyptindependent.com/
https://lepetitjournal.com/le-caire
https://www.mena.org.eg/
https://www.w3newspapers.com/lebanon/
https://www.w3newspapers.com/algeria/
https://www.w3newspapers.com/saudi-arabia/
https://english.ahram.org.eg/Portal/3/Business.aspx
https://gate.ahram.org.eg/Portal/44/%D8%B1%D9%8A%D8%A7%D8%B6%D8%A9.aspx
https://ar.w3newspapers.com/%D9%85%D8%B5%D8%B1/
https://www.w3newspapers.com/egypt/#top
https://www.facebook.com/sharer.php?u=https://www.w3newspapers.com/egypt/
https://x.com/share?url=https://www.w3newspapers.com/egypt/

https://diariorombe.es/
https://www.guinea-ecuatorial.net/
http://www.asodeguesegundaetapa.org/
https://www.guineainfomarket.com/
https://geconfidencial.blogspot.com/
https://www.eldiariodemalabo.com/
https://reliefweb.int/country/gnq
https://www.jeuneafrique.com/pays/guinee-equatoriale/

https://awate.com/
https://www.eritreadaily.net/
http://www.meskerem.net/
https://tesfanews.com/
https://zenazajel.net/
https://www.farajat.net/ar/
http://www.jeberti.com/
http://www.madote.com/
https://asenatv.com/
https://shabait.com/
http://raimoq.com/
https://adoulis.net/
https://www.asmarino.com/
http://dehai.org/
https://www.jeuneafrique.com/pays/erythree/

http://www.times.co.sz/
http://new.observer.org.sz/
http://www.swazilandnews.co.za/

https://www.ethiopianreporter.com/
https://www.capitalethiopia.com/
http://www.addisadmassnews.com/
https://mereja.com/index/
http://www.aigaforum.com/
https://newbusinessethiopia.com/
https://addisfortune.news/
https://ethiopiazare.com/
https://www.thereporterethiopia.com/
http://www.tadias.com/
https://ethiopianege.com/
https://zehabesha.com/
https://www.ezega.com/News/am/
https://www.ethiosports.com/
http://www.debteraw.com/
https://www.maledatimes.com/
https://ethiopiaforums.com/
https://www.tigraionline.com/
https://news.google.com/home?hl=en-ET&gl=ET&ceid=ET:en


https://www.union.sonapresse.com/
https://www.w3newspapers.com/france/
https://www.gabonews.com/
https://gabonactu.com/
https://gabonmediatime.com/
https://info241.com/
http://www.alibreville.com/
https://gaboneco.com/
http://www.gabonreview.com/
https://directinfosgabon.com/
https://fr.infosgabon.com/
https://www.infosplusgabon.com/
https://agpgabon.ga/
https://www.journaldugabon.com/

https://foroyaa.net/
https://thepoint.gm/
https://standard.gm/
https://www.allgambianews.com/
https://gainako.com/
https://www.fatunetwork.net/
http://www.kaironews.com/
https://gambia-today.com/
https://elegance.gm/
http://whatson-gambia.com/

https://www.graphic.com.gh/
https://dailyguidenetwork.com/
https://yen.com.gh/
https://theheraldghana.com/
https://www.ghpage.com/
https://ghanasoccernet.com/
https://www.pulse.com.gh/
https://www.modernghana.com/
https://thebftonline.com/
https://www.gbcghana.com/
https://www.ghbase.com/
https://www.ghanaweb.com/
https://citinewsroom.com/
https://www.thefinderonline.com/
https://www.businessghana.com/
https://newsghana.com.gh/
http://ghheadlines.com/
https://thechronicle.com.gh/
https://www.todaygh.com/
https://ghananewspage.com/
https://ghanamansports.com/
https://www.peacefmonline.com/
https://www.ghanastar.com/
http://www.reportghananews.com/
http://ghana360news.com/
https://3news.com/
https://gna.org.gh/

https://guineenews.org/
https://www.africaguinee.com/
https://aminata.com/
https://guineematin.com/
https://mediaguinee.org/
https://www.foot224.co/
https://www.gnakrylive.com/
https://actuguinee.org/
https://www.guinee360.com/
https://guineefoot.info/
http://www.guinee24.com/
http://www.kababachir.com/
https://www.guinee7.com/
https://guineelive.com/
https://kaloumpresse.com/
https://conakryinfos.com/
https://afrinews.org/
https://www.lelynx.net/

https://www.odemocratagb.com/
http://www.rispito.com/
https://conosaba.blogspot.com/
https://dokainternacionaldenunciante.blogspot.com/
https://faladepapagaio.blogspot.com/
https://guineendade.blogspot.com/
https://notabanca.blogspot.com/
https://bambaramdipadida.blogspot.com/
https://www.lejourguinee.com/

https://www.fratmat.info/
https://www.w3newspapers.com/france/
https://www.abidjan.net/
https://www.linfodrome.com/
https://www.aip.ci/
https://www.jeuneafrique.com/pays/cote-divoire/

https://nation.africa/kenya
https://www.standardmedia.co.ke/
https://www.tuko.co.ke/
https://www.ghafla.co.ke/ke/
https://mpasho.co.ke/
https://www.pulselive.co.ke/
https://www.businessdailyafrica.com/
https://www.kenyan-post.com/
https://www.the-star.co.ke/
https://www.news24.com/tags/places/kenya
https://www.kenya-today.com/
https://www.capitalfm.co.ke/
https://nairobiwire.com/
https://businesstoday.co.ke/
https://kenyannews.co.ke/
https://www.citizen.digital/
https://www.theeastafrican.co.ke/
https://www.kenyanews.go.ke/
https://www.mwakilishi.com/
https://nairobinews.nation.africa/
https://taifaleo.nation.co.ke/
https://breakingkenyanews.blogspot.com/
https://www.kbc.co.ke/


Lesotho
https://sundayexpress.co.ls/
https://www.thepost.co.ls/
https://lestimes.com/
https://informativenews.co.ls/
https://publiceyenews.com/
https://www.jeuneafrique.com/pays/lesotho/

https://www.liberianobserver.com/
https://www.emansion.gov.lr/
https://thenewdawnliberia.com/
https://bushchicken.com/
https://plusliberia.com/
https://frontpageafricaonline.com/
https://gnnliberia.com/
https://themonroviatimes.com/
https://smartnewsliberia.com/
https://gossipliberia.com/
https://www.theperspective.org/

https://www.libyaakhbar.com/
https://www.afrigatenews.net/
https://almarsad.co/
http://www.newlibya.net/
https://akhbarlibya24.net/
https://libyaherald.com/
https://libyaobserver.ly/
https://www.almusallh.ly/
https://www.libyanexpress.com/
https://libya-businessnews.com/
https://febp.ly/
https://www.eanlibya.com/
http://alwasat.ly/
https://libyaschannel.com/
https://www.218tv.net/
https://lana.gov.ly/
https://www.almukhtaralarabi.com/
https://www.libyamonitor.com/
http://libyaalsalam.net/
https://www.elkhabar.ly/
https://www.libya-news.com/

https://lexpress.mg/
https://www.madagascar-tribune.com/
https://midi-madagasikara.mg/
https://newsmada.com/
https://www.moov.mg/
https://laverite.mg/
https://actu.orange.mg/
https://www.lagazette-dgi.com/
https://www.w3newspapers.com/france/
https://www.madagate.org/
https://latribune.cyber-diego.com/
https://matv.mg/
http://www.gvalosoa.net/
http://www.madonline.com/
https://www.infokmada.org/

https://mwnation.com/
https://www.nyasatimes.com/
https://www.maravipost.com/
https://times.mw/
https://www.bizmalawi.com/
https://www.capitalradiomalawi.com/
https://www.faceofmalawi.com/
https://malawi24.com/
https://www.malawivoice.com/
https://www.maraviexpress.com/
https://www.businessmalawi.com/
https://malawifreedomnetwork.com/
https://www.radiomaria.mw/
https://www.zodiakmalawi.com/

https://lessor.ml/
https://www.w3newspapers.com/france/
https://www.maliweb.net/
http://www.abamako.com/
https://maliactu.net/
https://malijet.com/
http://bamada.net/
https://www.studiotamani.org/
https://www.journaldumali.com/
https://www.afribone.com/
http://mali-web.org/
https://www.info-matin.ml/
https://malizine.com/
https://amap.ml/
https://malimedia.net/
https://lexpressdumali.com/
https://mali-info.net/

http://www.lecalame.info/
https://saharamedias.net/
https://www.alakhbar.info/
https://rimnow.com/
https://essahraa.net/
https://www.alwiam.info/
https://www.rimtoday.net/
https://www.atlasinfo.info/
https://taqadoum.mr/
https://tawary.com/
https://meyadin.net/
http://mauriactu.info/ar/
http://souhoufi.com/
https://essaha.net/
http://elwatan.info/
https://mourassiloun.com/
http://mauriweb.info/ar/
http://www.essirage.net/
https://cridem.org/
https://tvm.mr/fr/
http://www.lauthentic.info/
http://elhourriya.net/
https://alikhbari.net/
https://www.alkhabar.mr/
http://anbaa.info/
https://kassataya.com/
https://anbaatlas.com/
http://elmourabiton.tv/
https://www.radiomauritanie.mr/
https://www.ami.mr/
https://www.journaltahalil.com/
https://www.maurimedia.net/

https://lexpress.mu/
https://lexpress.mu/
https://www.lemauricien.com/
https://www.lemauricien.com/
https://defimedia.info/
https://defimedia.info/
https://5plus.mu/
https://5plus.mu/
https://www.mauritiustimes.com/
https://sundaytimesmauritius.com/
https://www.business-magazine.mu/
https://ecoaustral.com/
https://starpress.info/
https://www.lemauricien.com/category/week-end/
https://defimedia.info/
https://defimedia.info/categorie/news-sunday
https://ionnews.mu/
https://www.channelnews.mu/
https://inside.news/
https://newsmoris.com/
https://www.maurice-info.mu/
https://www.peoplepress.co/
https://live.mega.mu/
https://www.mbcradio.tv/
https://live.radioplus.mu/
https://topfm.mu/
https://r1.mu/
https://www.wazaa.mu/

https://lematin.ma/
https://assabah.ma/
https://www.w3newspapers.com/arabic/
https://www.almaghribia.ma/
https://www.leconomiste.com/
https://www.w3newspapers.com/france/
https://lanouvelletribune.info/
https://www.lavieeco.com/
https://aujourdhui.ma/
https://ar.le360.ma/
https://www.akhbarona.com/
https://www.barlamane.com/
https://tanja24.com/
https://rue20.com/
https://kech24.com/
https://www.maroc-hebdo.com/
https://www.ahdath.info/
https://www.aljamaa.net/
https://www.cawalisse.com/
https://www.hespress.com/
https://ar.hibapress.com/
https://lnt.ma/
https://www.tanja7.com/
https://www.agora.ma/
https://www.maghress.com/
https://casaoui.ma/
https://www.chtoukapress.com/
https://www.yabiladi.com/
https://presstetouan.com/
https://telquel.ma/
https://www.libe.ma/
https://www.goud.ma/
https://www.almountakhab.com/
https://www.menara.ma/
https://www.nadorcity.com/
https://www.moroccoworldnews.com/
https://www.atlasscoop.com/
https://febrayer.com/
https://www.h24info.ma/
https://www.oujdacity.net/
https://souss24.com/
https://www.bladi.net/
https://www.zagorapress.com/
https://tanjanews.com/
https://alyaoum24.com/
https://kifache.com/
https://agadir24.info/
https://www.lopinion.ma/
http://www.eljadida24.com/ar/
https://marrakech7.com/
http://www.azilal24.com/
https://zagoranews.com/
https://soussplus.com/
https://dalil-rif.com/
https://article19.ma/ar/
https://www.lereporter.ma/
https://anfaspress.com/
https://www.alalam.ma/
https://www.medi1.com/
https://www.alakhbar.press.ma/
http://bayanealyaoume.press.ma/
https://www.hitradio.ma/fr
https://medradio.ma/
https://www.map.ma/

https://www.jornalnoticias.co.mz/
https://www.w3newspapers.com/portugal/
https://www.mmo.co.mz/
https://cartamz.com/
https://verdade.co.mz/
https://clubofmozambique.com/
https://www.folhademaputo.co.mz/
https://portalmoznews.com/
https://stop.co.mz/
https://www.jornaldesafio.co.mz/
https://jornaltxopela.com/
https://zitamar.com/
https://www.jornaldomingo.co.mz/
https://www.tvm.co.mz/
https://www.portaldogoverno.gov.mz/

https://www.namibian.com.na/
https://neweralive.na/
https://www.az.com.na/
https://www.w3newspapers.com/germany/
https://www.republikein.com.na/
https://economist.com.na/
https://www.namibiansun.com/
https://informante.web.na/
https://www.observer24.com.na/
https://www.caprivivision.com/
https://www.namibtimes.net/
http://www.thevillager.com.na/
https://www.nampa.org/
https://www.nbc.na/
https://www.k7.com.na/
https://radiowave.com.na/
https://www.namibianewsdigest.com/
https://99fm.com.na/
https://kundana.com.na/
https://news.google.com/home?hl=en-NA&gl=NA&ceid=NA:en

http://www.news.aniamey.com/
https://www.actuniger.com/
https://www.nigerdiaspora.net/
https://www.lesahel.org/
https://tamtaminfo.com/
https://www.nigerinter.com/
https://www.iciniger.com/
https://airinfoagadez.com/
https://nigerexpress.info/
https://www.journalduniger.com/

https://punchng.com/
https://www.vanguardngr.com/
https://thenationonlineng.net/
https://guardian.ng/
https://www.thisdaylive.com/
https://dailytrust.com/
https://tribuneonlineng.com/
https://thesun.ng/
https://leadership.ng/
https://newtelegraphng.com/
https://independent.ng/
https://blueprint.ng/
https://www.thepointng.com/
https://nationaldailyng.com/
https://dailytimesng.com/
https://www.peoplesdailyng.com/
https://nigerianpilot.net/
https://authorityngr.com/
https://www.nationalaccordnewspaper.com/
https://championnews.com.ng/
https://www.thetidenewsonline.com/
https://www.thetidenewsonline.com/
https://osundefender.com/
https://osundefender.com/
https://nigerianobservernews.com/
https://nigerianobservernews.com/
https://nationalnetworkonline.com/
https://nationalnetworkonline.com/
https://pmnewsnigeria.com/
https://freshangleng.com/
https://theabujainquirer.com/
https://www.thepointersnewsonline.com/
https://www.thehopenewspaper.com/
https://pioneernewsng.com/
https://www.theheraldnews.ng/
https://aminiya.ng/
https://hausa.premiumtimesng.com/
https://hausa.leadership.ng/
https://hausa.legit.ng/
https://www.bbc.com/yoruba
https://www.bbc.com/igbo
https://businessday.ng/
https://businessday.ng/
https://www.nigeriacommunicationsweek.com.ng/
http://businessnews.com.ng/
https://www.completesports.com/
https://www.allnigeriasoccer.com/
https://www.w3newspapers.com/magazines/soccer/
https://sportinglife.ng/
https://brila.net/
https://scorenigeria.com.ng/
https://owngoalnigeria.com/
https://sportingtribune.com/
https://www.aclsports.com/
https://www.legit.ng/
https://dailypost.ng/
https://saharareporters.com/
https://www.premiumtimesng.com/
https://www.thecable.ng/
https://www.naijanews.com/
https://www.pulse.ng/
https://www.lindaikejisblog.com/
https://nairametrics.com/
https://gazettengr.com/
https://thewhistler.ng/
https://www.icirnigeria.org/
https://www.ripplesnigeria.com/
https://dailynigerian.com/
https://techcabal.com/
https://thewillnews.com/
https://theeagleonline.com.ng/
https://thecitizenng.com/
https://nigerianbulletin.com/
https://nigeriaworld.com/
https://www.nigerianeye.com/
https://politicsnigeria.com/
https://ynaija.com/
https://www.okay.ng/
https://247ureports.com/
https://www.gistmania.com/
https://www.thenigerianvoice.com/
https://www.hynaija.com/
https://www.thinkersnewsng.com/
https://www.channelstv.com/
https://www.galaxytvonline.com/
https://freedomradionig.com/
https://radionigeria.gov.ng/
https://www.tvcnews.tv/
https://www.arise.tv/
https://von.gov.ng/
https://nannews.ng/
https://www.nigerianwatch.com/

https://www.newtimes.co.rw/
https://umuryango.rw/eng/
https://inyarwanda.com/
https://umuseke.rw/
https://igihe.com/
https://www.kigalitoday.com/
https://www.ktpress.rw/
https://imvahonshya.co.rw/
https://www.rba.co.rw/
https://www.therwandan.com/
https://www.intyoza.com/
https://www.rnanews.com/
https://rugali.com/
https://rwandatoday.africa/
https://rwandaises.com/
https://www.radiomaria.rw/
https://www.musabyimana.net/
https://www.jambonews.net/en/
https://www.lerwandais.com/
https://www.gov.rw/

http://www.jornaltransparencia.st/
https://www.telanon.info/
https://stpdigital.net/
http://www.jornaltropical.st/
https://www.jeuneafrique.com/pays/sao-tome-et-principe/

https://lequotidien.sn/
https://www.enqueteplus.com/
https://www.seneweb.com/
https://senego.com/
https://www.dakaractu.com/
https://galsen221.com/
https://www.leral.net/
https://aps.sn/
https://walf-groupe.com/
https://senegal7.com/
https://www.metrodakar.net/
https://www.buzzsenegal.com/
https://www.senenews.com/
https://www.dakarbuzz.net/
https://www.igfm.sn/
https://wiwsport.com/
https://www.dakarmatin.com/
https://www.xalimasn.com/
https://www.rewmi.com/
https://www.pressafrik.com/
https://www.ndarinfo.com/
https://www.seneplus.com/
https://samarew.com/
https://senegaldirect.com/
https://lesoleil.sn/
https://www.w3newspapers.com/france/
https://www.rts.sn/
https://www.planete-senegal.com/
https://actusen.sn/
https://www.lejecos.com/
https://www.senedirect.tv/
https://www.vipeoples.net/
https://laviesenegalaise.com/
https://www.socialnetlink.org/
https://www.koldanews.com/
https://www.setal.net/
https://www.dakarmidi.net/
https://www.senxibar.com/
https://kewoulo.info/
https://teranganews.sn/

https://www.nation.sc/
http://www.thepeople.sc/
https://www.sbc.sc/
https://www.fourseasons.com/magazine/
https://seychelles.com/home
http://www.seychellesweekly.com/
https://www.todayinseychelles.com/
https://www.jeuneafrique.com/pays/seychelles/
https://en.wikipedia.org/wiki/Seychelles
https://reliefweb.int/country/syc

https://www.thesierraleonetelegraph.com/
https://sierraexpressmedia.com/
https://www.politicosl.com/
https://globaltimes-sl.com/
https://cocorioko.net/
https://awokonewspaper.com/
https://www.switsalone.com/
https://statehouse.gov.sl/
https://theorganiser.net/
https://salonepost.com/
https://www.thepatrioticvanguard.com/
https://www.sierraleonepress.com/
https://sierraleonelive.com/
https://www.critiqueecho.com/
https://thecalabashnewspaper.com/
https://nightwatchsl.com/

https://www.hiiraan.com/
https://www.simbanews.net/
https://www.caasimada.net/
https://jowhar.com/
https://www.allbanaadir.org/
https://boramanews.com/
https://goobjoog.com/
https://www.garoweonline.com/
https://wardheernews.com/
https://somalilandtoday.com/
https://www.dayniiile.com/
https://waagacusub.com/
https://puntlandpost.net/
https://horseedmedia.net/
https://allsbc.com/
https://radiomuqdisho.so/

https://www.citizen.co.za/
https://www.netwerk24.com/dieburger
https://iol.co.za/the-star/
https://isolezwe.co.za/
https://www.sowetan.co.za/
https://www.businessday.co.za/
https://iol.co.za/capetimes/
https://iol.co.za/capeargus/
https://iol.co.za/mercury/
https://iol.co.za/dailynews/
https://witness.co.za/
https://www.theherald.co.za/
https://www.dailydispatch.co.za/
https://mg.co.za/
https://iol.co.za/ios/
https://iol.co.za/thepost/
https://www.sajr.co.za/
https://www.son.co.za/
https://www.citizen.co.za/lowvelder/
https://www.georgeherald.com/
https://www.citizen.co.za/rekord/
https://www.citizen.co.za/vaalweekblad/
https://www.citizen.co.za/zululand-observer/
https://www.citizen.co.za/potchefstroom-herald/
https://www.citizen.co.za/krugersdorp-news/
https://www.citizen.co.za/middelburg-observer/
https://www.citizen.co.za/ridge-times/
https://dailyvoice.co.za/
https://dfa.co.za/
https://www.citizen.co.za/alberton-record/
https://www.grocotts.co.za/
https://www.citizen.co.za/bedfordview-edenvale-news/
https://www.citizen.co.za/south-coast-herald/
https://www.citizen.co.za/berea-mail/
https://www.citizen.co.za/south-coast-sun/
https://risingsunnewspapers.co.za/
https://www.citizen.co.za/african-reporter/
https://www.citizen.co.za/alex-news/
https://www.citizen.co.za/letaba-herald/
https://www.citizen.co.za/kempton-express/
https://www.zoutnet.co.za/
https://theannouncer.co.za/
https://www.bloemfonteincourant.co.za/
https://www.citizen.co.za/benoni-city-times/
https://www.citizen.co.za/boksburg-advertiser/
https://www.citizen.co.za/brakpan-herald/
https://www.mosselbayadvertiser.com/
https://www.northwestnewspapers.co.za/klerksdorprecord/
https://www.platinumweekly.co.za/
https://www.knysnaplettherald.com/
https://www.oudtshoorncourant.com/
https://www.citizen.co.za/northern-natal-news/
https://www.citizen.co.za/sedibeng-ster/
https://witsvuvuzela.com/
https://pdby.co.za/
https://varsitynewspaper.substack.com/
https://www.timeslive.co.za/
https://iol.co.za/
https://www.snl24.com/dailysun
https://www.news24.com/citypress
https://www.ewn.co.za/
https://www.news24.com/
https://briefly.co.za/
https://www.thesouthafrican.com/
https://www.citizen.co.za/review-online/
https://maroelamedia.co.za/
https://www.dailymaverick.co.za/
https://southafricatoday.net/
https://www.politicsweb.co.za/
https://mayihlomenews.co.za/
https://www.polity.org.za/
https://www.thegremlin.co.za/
https://iafrica.com/
https://www.sagoodnews.co.za/
https://news.co.za/
https://cbn.co.za/
https://businesstech.co.za/news/
https://www.businessinsider.com/
https://www.moneyweb.co.za/
https://www.news24.com/business
https://www.biznews.com/
https://www.sharenet.co.za/
https://www.engineeringnews.co.za/
https://www.itweb.co.za/
https://techcentral.co.za/
https://www.news24.com/sport
https://supersport.com/
https://www.soccerladuma.co.za/
https://www.kickoff.com/
https://www.enca.com/
https://www.sabcnews.com/sabcnews/
https://www.newzroomafrika.tv/
https://www.cnbcafrica.com/
https://www.sanews.gov.za/
https://africannewsagency.com/
https://www.cajnewsafrica.com/
https://groundup.org.za/
https://www.facebook.com/sharer.php?u=https://www.w3newspapers.com/south-africa/
https://x.com/share?url=https://www.w3newspapers.com/south-africa/

https://www.newsudanvision.com/
https://ssnanews.com/
https://radiotamazuj.org/en
https://sudantribune.com/
https://hotinjuba.com/
https://www.southsudanliberty.com/news/
https://ssnewsnow.com/
https://www.talkofjuba.com/
https://pachodo.org/

https://sudaneseonline.com/
https://www.w3newspapers.com/arabic/
https://www.alnilin.com/
https://www.sudanakhbar.com/
https://bajnews.net/
https://rakobanews.com/
https://www.cover-sd.com/
https://www.sudaress.com/
https://www.alrakoba.net/
https://sudanile.com/
https://www.albawaba.com/
https://sudantribune.com/
https://www.w3newspapers.com/france/
https://suna-sd.net/en
https://www.dabangasudan.org/en
https://www.altaghyeer.info/ar/
https://arabic-media.com/
https://www.assayha.net/
https://www.alhamish.com/
https://sudanjem.com/
https://alsudaninews.com/
https://www.meed.com/countries/sudan/
https://radiotamazuj.org/en

https://www.thecitizen.co.tz/
https://dailynews.co.tz/
https://habarileo.co.tz/
https://www.mwanaspoti.co.tz/
https://bongo5.com/
https://globalpublishers.co.tz/
https://dar24.com/
https://mwanahalisionline.com/
https://www.jamhurimedia.co.tz/
http://www.zanzinews.com/
https://ippmedia.com/the-guardian
https://www.tbc.go.tz/
https://www.itv.co.tz/
http://businesstimes.co.tz/
https://www.ippmedia.com/en

https://letempstg.com/
https://icilome.com/
https://togotribune.com/
https://togobreakingnews.info/
https://www.togofirst.com/en
https://togoweb.net/
https://autogo.tg/
https://www.27avril.com/
https://togopresse.tg/
https://afreepress.info/
https://www.togoactualite.com/
https://www.savoirnews.tg/
https://togomedia24.com/
https://togotimes.info/
https://togoreveil.com/
https://www.lomeinfos.com/
https://togoenlive.info/
https://lanouvelletribune.net/
https://togo24.net/
https://www.independantexpress.net/
https://libertetogo.info/
http://www.letogolais.com/
https://www.republicoftogo.com/

https://lapresse.tn/
https://www.w3newspapers.com/france/
https://www.tap.info.tn/
https://www.babnet.net/
https://www.tuniscope.com/ar/
https://kapitalis.com/
https://www.businessnews.com.tn/
https://www.tunisienumerique.com/
https://ar.tunisienumerique.com/
https://www.assabahnews.tn/ar/
https://realites.com.tn/fr/
https://www.alchourouk.com/
https://ar.lemaghreb.tn/
https://www.tunisiefocus.com/
https://www.leconomistemaghrebin.com/
https://www.webdo.tn/fr
https://directinfo.webmanagercenter.com/
https://www.webmanagercenter.com/
https://africanmanager.com/
https://assarih.com/
https://tunisie.co/
https://tunisie14.tn/
http://www.tdailynews.net/
https://www.nessma.tv/ar
http://www.watania1.tn/
https://journalistesfaxien.tn/
https://www.turess.com/
https://www.kawarji.com/
https://www.leaders.com.tn/
https://www.espacemanager.com/
http://www.tekiano.com/
https://nawaat.org/
https://www.tunisien.tn/
https://tunisie-telegraph.com/
https://www.marhba.com/
https://www.elhiwarettounsi.com/ar/
http://www.radiotunisienne.tn/
https://www.mosaiquefm.net/ar/

https://www.newvision.co.ug/
https://www.monitor.co.ug/
https://www.observer.ug/
https://redpepper.co.ug/
https://www.bukedde.co.ug/
https://www.independent.co.ug/
https://chimpreports.com/
https://nilepost.co.ug/
https://softpower.ug/
https://www.howwe.ug/
https://www.pmldaily.com/
https://bigeye.ug/
https://www.sqoop.co.ug/
https://www.watchdoguganda.com/
https://newslexpoint.com/
https://ugandandiasporanews.com/
https://eagle.co.ug/
https://www.thegrapevine.co.ug/
https://sunrise.ug/
https://ugbusiness.com/
https://www.256businessnews.com/
https://www.mediacentre.go.ug/
https://theinvestigatornews.com/
https://www.busiweek.com/
https://flashugnews.com/

https://www.spsrasd.info/
https://rasd.tv/
http://www.sahara-online.net/
https://www.saharawi.net/
https://porunsaharalibre.org/
https://wsrw.org/en
https://ceas-sahara.es/
http://www.corcas.com/
https://saharaoccidental.blogspot.com/
https://reliefweb.int/country/esh

https://www.lusakatimes.com/
https://www.times.co.zm/
https://www.daily-mail.co.zm/
https://diggers.news/
https://zambianeye.com/
https://www.mwebantu.com/
https://zambianobserver.com/
https://zambianfootball.co.zm/
https://dailynationzambia.com/
https://zambia.co.zm/
https://lusakastar.com/
https://zedgossip.net/
https://www.lusakavoice.com/
https://zambianews365.com/
https://www.zambiainvest.com/
https://www.openzambia.com/
https://theglobeonline.news/
https://www.zambianpolitics.com/
http://www.lowdownzambia.com/

https://www.heraldonline.co.zw/
https://www.newsday.co.zw/
https://dailynews.co.zw/
https://fingaz.co.zw/
https://www.sundaymail.co.zw/
https://www.kwayedza.co.zw/
https://www.sundaynews.co.zw/
https://www.thezimbabwean.co/
https://www.heraldonline.co.zw/bmetro/
https://www.thestandard.co.zw/
https://masvingomirror.com/
https://www.chronicle.co.zw/
https://www.heraldonline.co.zw/hmetro/
https://www.newzimbabwe.com/
https://www.thepatriot.co.zw/
https://www.manicapost.co.zw/
https://tellzim.com/
http://www.businessdaily.co.zw/
https://iharare.com/
https://www.myzimbabwe.co.zw/
https://www.zimbabwesituation.com/
https://www.thezimbabwenewslive.com/
https://www.zimeye.net/
https://bulawayo24.com/
https://www.thezimbabwemail.com/
https://nehandaradio.com/
https://mbaretimes.com/
https://www.zimbabwestar.com/
https://www.zbcnews.co.zw/
https://www.hararepost.co.zw/en/
https://www.businessweekly.co.zw/
https://thesunnews.co.zw/
https://insiderzim.com/
https://zwnews.com/
https://www.w3newspapers.com/zimbabwe/magazines/
https://www.w3newspapers.com/south-africa/
https://www.theindependent.co.zw/
https://fingaz.co.zw/
https://www.soccer24.co.zw/
https://www.heraldonline.co.zw/tag/sports/
https://www.newsday.co.zw/category/sport
https://iharare.com/
"""

# ---------- helpers ----------
def url_normalise(url: str) -> str:
    """Lower-case + remove trailing slash for uniqueness."""
    return url.strip().rstrip("/").lower()

def def guess_meta(url: str):
    """Return explicit lang per country block."""
    url = url.lower()
    if any(tld in url for tld in (".ao", ".cv", ".mz")):          # lusophone
        return "pt"
    if any(tld in url for tld in (".dz", ".ma", ".tn", ".ly")):   # arabophone
        return "ar"
    if any(tld in url for tld in (".eg", ".sd", ".so", ".dj")):   # arabic
        return "ar"
    if any(tld in url for tld in (".bj", ".bf", ".ci", ".tg", ".ml", ".sn", ".cd", ".cg", ".ga", ".cf", ".td", ".cm", ".gq")):
        return "fr"
    if any(tld in url for tld in (".ng", ".gh", ".lr", ".sl", ".gm", ".ke", ".ug", ".tz", ".rw", ".bi", ".mw", ".zm", ".zw", ".bw", ".na", ".sz", ".ls", ".za")):
        return "en"
    if any(tld in url for tld in (".et", ".er")):                 # amharic / tigrinya
        return "am"        # or "en" if you prefer English default
    # fallback
    return "en"

def probe(url: str):
    """Return (url, status_ok, reason)."""
    try:
        resp = requests.head(url, timeout=TIMEOUT, allow_redirects=True)
        ok = 200 <= resp.status_code < 400
        return url, ok, resp.status_code
    except Exception as e:
        return url, False, str(e)

# ---------- main ----------
def main():
    # 1.  parse raw block → unique list
    candidates = list({url_normalise(u): u for u in RAW_HTTPS.strip().splitlines() if u.startswith("http")}.values())

    # 2.  load existing YAML so we can skip duplicates
    if os.path.exists(SRC_YAML):
        with open(SRC_YAML, encoding="utf8") as f:
            existing = {url_normalise(entry["url"]): entry for entry in yaml.safe_load(f) or []}
    else:
        existing = {}

    new_urls = [u for u in candidates if url_normalise(u) not in existing]
    print(f"Unique new URLs to test: {len(new_urls)}")

    # 3.  probe in parallel
    clean = []
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futures = {ex.submit(probe, u): u for u in new_urls}
        for fut in as_completed(futures):
            url, ok, reason = fut.result()
            if ok:
                clean.append(url)
            else:
                print(f"[SKIP] {url}  –  {reason}")

    print(f"Responsive URLs kept: {len(clean)}")

    # 4.  build yaml entries
    entries = []
    for url in clean:
        entries.append({
            "name": urlparse(url).netloc.replace("www.", ""),
            "url":  url,
            "type": "rss",               # collectors fall back to scrape if no rss
            "lang": guess_meta(url)
        })

    # 5.  append to file
    with open(SRC_YAML, "a", encoding="utf8") as f:
        yaml.safe_dump(entries, f, allow_unicode=True, sort_keys=False)
    print(f"Appended {len(entries)} records → {SRC_YAML}")

if __name__ == "__main__":
    main()
