"""
Descarga logos de Clearbit para todos los dominios del ecosistema.
Guarda en pilot/logos/<domain>.png
Saltea los que ya existen.
"""
import os, time, urllib.request, urllib.error

DOMAINS = [
    "1200.vc","500.co","abiocontrollers.com","ace.vc","aceleradoralitoral.com.ar",
    "activaq.cl","aegro.com.br","agesbioactive.com","agree.ag","agrion.ag",
    "agritechbolivia.com","agrivalle.com.br","agrobit.io","agrojustoinc.com",
    "agrologia.co","agronow.com.br","agrorganica.com","agroscan.ec","agrosmart.com.br",
    "agrosustain.com.mx","agrourbana.ag","aguablancaseafood.com","aimirimsti.com.br",
    "aintech.cl","aircapital.vc","alecrim.bio","alexia.vc","algaebioplus.com",
    "algenis.cl","alkemio.tech","alytixbiotech.com","amador.vc","amplify-dynamics.com",
    "andesbiotec.com","antarka.bio","antom.la","apasomics.com","apexzymes.com",
    "aplifebiotech.com","aptah-bio.com","aptah.bio","aquabio.cl","aquabyte.ai",
    "aquacapital.com.br","araucaria.vc","arauco.com","aravanlabs.com.uy","arcomed.com",
    "ardan-pharma.com","argentag.com","argentina.gob.ar","asclepii.com","ascribebio.com",
    "atacamabiomaterials.com","atlantico.vc","auravant.com","autemtherapeutics.com",
    "avatarmedtech.co","avedian.health","axventures.com","ayuvant.com","bago.com.ar",
    "barn.ag","beamcroptech.com","beeflow.com","beepsaude.com.br","beetechnology.cl",
    "bemagro.cloud","bentenbiotech.com","bialtec.co","bidlab.org","biiosmart.com",
    "bio-metallum.com","bio-plastix.com","biobreyer.com.br","biocell.mx",
    "biocentis.com.br","bioceres.com.ar","biodiverso.com.br","bioelementsla.com",
    "bioeutectics.com","biofab.com.pe","biofabrica.com.mx","biofactory.com.br",
    "biofresh.com.br","biogenesisbago.com","bioheuris.com","bioinagro.com.br",
    "biolifeinnovations.com","biolinker.tech","biomar.cr","biomas.com","biomerieux.com",
    "biominas.org.br","bionativa.cl","bioplast.com.br","bioplaster-research.com",
    "bioprocauto.com.br","bioproducts.co","bioram.com.mx","biorefinery.com.br",
    "biorgani.tech","biosens.tech","biosidus.com.ar","biosmatter.com","biosolvit.com",
    "biosynaptica.com","biotalife.com","biotechcr.com","biotecnofe.com.ar",
    "bioticsol.com","biotimize.com.br","biotrop.com.br","biowit.mx","bitgenia.com",
    "bitmec.com","blepsvision.com","bloomcare.com.br","bluehorizonventures.com",
    "bndes.gov.br","bossanova.vc","botanicalsolution.com","brain4care.com","brinc.io",
    "bruna.ai","bsafebiotech.com","bybug.io","bymycell.com.br","caf.com","calice.ai",
    "calicebiotech.com","caligenia.com","canary.com.br","cantos.vc","caraov.com",
    "carbonext.com.br","carigenetics.com","celer.ind.br","cell.farm","cellculture.com.br",
    "cellertz.com","cellmeat.com.br","cellrep.bio","cellsforcells.cl","cellter.cl",
    "celluris.com","cellva.com","cenibiot.ac.cr","cephabio.com","cerradox.com",
    "checkplant.com.br","chileglobalventures.cl","circatherapeutics.com","cites-gss.com",
    "clearagro.com","codebreaker.bio","conservation.org","consiste.com.br",
    "contechbrasil.com","copper3d.com","copptech.com","corfo.cl","corpogen.org",
    "corsync.com.br","corteva.com","courageousland.com","cowmed.com.br","cropguard.cl",
    "cryosmetics.com","curbwaste.com","cyanomin.bio","daeki.cl","daluscapital.com",
    "decoy.bio","deepagro.com","delee.co","detxmol.com.ar","devalor.cl",
    "diagnosis-bt.com","diagtech.com.mx","digifarmz.com","dimitra.io","dioxd.com",
    "domoinvest.com.br","doneproperly.co","dragones.vc","draper.vc","drapercygnus.com",
    "dynamo.com.br","earthoceanfarm.com","eatableadventures.com","eatcloud.co",
    "ecbiotech.com","ecoa.capital","ecosativa.net","ecoshellmx.com","ecotrace.global",
    "einsted.bio","eiwa.ag","ejidoverde.com","elytronbiotech.com","endinv.com",
    "endurance28.vc","enzyvo.com","eolo-pharma.com","epicca.bio","ergobiotech.com",
    "eternal.bio","eurofarma.com","evacenter.com","exactascience.com","examedi.cl",
    "exomas.co","eywa.bio","f4f.cl","fabns.com.br","fecundis.com","feedvax.com",
    "fenventures.com","fermentlab.com.br","fermentlabs.co","fieldfactors.com.mx",
    "fkbiotec.com.br","formafoods.mx","fungicontrol.co","fungilife.net","futr.bio",
    "future.ventures","futurecow.com.br","galtec.ar","gameet.life","gaveainvest.com.br",
    "gen-t.co","geneprodx.com","generalcatalyst.com","genialcare.com.br","genica.com.br",
    "gentec.com.mx","gigablue.co","giraffebio.com","globalnano.mx","glocalfund.com",
    "glucogear.io","glycox.bio","granatumbioworks.com","greenrock.vc","greenxpolab.com",
    "gridexponential.com","growpack.bio","grupo-bios.co","grupodiagnosticoaries.com",
    "grupoinsud.com","gvangels.com.br","hapiseeds.com.br","hatch.blue",
    "hawthornefoodventures.com","healthpoint.bo","hemhealthtech.com","hemoalgae.com",
    "heritas.com.ar","hexemb.io","hiamet.com","hifglobal.com","hoobox.one",
    "horizonsventures.com","huiroregenerativo.com","huna-ai.com","hybridon.com.ar",
    "ictiobiotic.com","idbinvest.org","ideelab.com.br","ifad.org","ifc.org",
    "imeve.com.br","inbioar.com","inceres.com.br","indiebio.co","inedita.bio",
    "infoodprotein.com","inmet.com.ar","inmunova.com","innercosmos.ai","innmetec.co",
    "innogen.capital","innova-space.com","inventure.fi","isobar.agr.br","jica.go.jp",
    "kaete.com.br","kamayventures.com","kaszek.com","kayyakventures.com","keclon.com",
    "kheiron.com.ar","kigui.io","kilimo.com","koji.com.co","koltin.mx","kptl.com.br",
    "kran-nanobubble.com","krilltech.com.br","krtlbiotech.com","kurabiotech.com",
    "labtronics.net","lanxcapital.com.br","laturbina.com.ar","laurus.bio","lavca.org",
    "leftlane.com","levitamagnetics.com","levyabio.com","lifepack.co","lightsmith.com",
    "limay.bio","lindalifetech.com","livingink.co","lowercarbon.com","luyef.com",
    "mabxience.com","magentabiolabs.com","mavios.ai","mendelics.com.br",
    "merkenbiotech.cl","mesenchyalt.com.ar","metonai.com","michroma.co",
    "microbiota.com.br","microendo.com.mx","microgenesis.net","microlabs.com.mx",
    "micromeat.com","minerba.ec","mirscience.bio","modelosmedicos.com","mombak.com",
    "monashees.com.br","montecaldera.com","moolecscience.com","moondobiotech.com",
    "motivia.health","movet.co","movinvestimentos.com.br","multiplaihealth.com",
    "myvac.com.br","naiad.com.br","nalca.bio","nanoblast.com.mx","nanofreeze.com.co",
    "nanogrowbiotech.com","nanoingreen.com","nanopharmacia.com","nanoprox.com",
    "nanotica.com.ar","nanotransfer.bio","nanovetores.com.br","nat4bio.com","nativas.la",
    "naturannova.com","nchemi.com.br","nemacontrol.com.br","neocellbiotech.com",
    "neocroptech.com","neomed.com.br","neoprospecta.com","neuralmed.ai","neurognos.com",
    "newtopia.vc","nexxto.com","nintx.com.br","novagenic.com","novalact.com",
    "nunatakbio.com","nutrissis.bio","olhododono.agr.br","omica.bio","oncoprecision.bio",
    "onevc.vc","ospraie.com","outpost.bio","oxygea.com.br","pampastart.com","panarum.com",
    "pannextherapeutics.com","patbio.com","pathovet.cl","peptidus.com.br",
    "pewmaninnovation.net","pfgrowth.com","phage-lab.com","pharmalens.com.br",
    "photio.cl","phpbiotech.com.br","phylumtech.com","plantverd.com","poasbioenergy.com",
    "polybion.bio","porsche.com","positiveventures.com","powfoods.cl","praxisbiotech.com",
    "primatec.com.br","proinpa.org","promip.agr.br","prosperia.health","protera-bio.cl",
    "protiva.bio","puna.bio","qnity.bio","quantis.bio","qumirnano.com","radbiopharm.com",
    "re.green","receptabio.com.br","recirculab.cl","recombinebiotech.com.br","reddot.bio",
    "rizoflora.com.br","rnatech.com.ar","rumina.com.br","ruuts.la","salkantay.vc",
    "salmoss.cl","satellogic.com","savefruitcorp.com","saviaventures.com","scintia.com",
    "scitherm.bio","seedmatriz.com","seedtech.cl","selectivity.life","semionbio.com",
    "sensix.ag","sf500.org","silichem.ec","sima.ag","singlestrand.com","siquimia.com",
    "sistema.bio","solenagreen.com","solfium.com","solinftec.com","solubio.agr.br",
    "sosv.com","soygreen.bio","speclab.com.br","spectrainvest.com","speratum.com",
    "spherebio.co","spventures.com.br","stamm.bio","strider.ag","svb.com",
    "swebolbiotech.bo","sylvarum.co","symbiomics.com.br","syocin.com","tarvos.ag",
    "taugc.com.br","teledx.org","tensor.care","terragene.com","tesabio.ai",
    "theganeshalab.com","thegef.org","thelivegreen.co","theravx.com","thermy.mx",
    "theyieldlablatam.com","thyroidprint.com","tierrademonte.com","tismoo.us",
    "tissuelabs.com","tissuenova.mx","tomorrowco.bio","tracestory.com","treevia.com.br",
    "ucrop.it","unimadx.com","untech.bio","updairy.co","usv.com","valorcapitalgroup.com",
    "varanacapital.com","vaxinz.com","velozbio.com","venturance.cl","vesperventures.com.br",
    "vetpix.com.br","viewmind.com","virtechbio.com","vitalesagro.com.br","voxcapital.com.br",
    "vyrobio.com","waterlemon.vc","waterplan.com","wayakgroup.com","webio.bio","welii.com",
    "wiagro.com","wiseconn.cl","wiselatinamerica.com","wseeds.io","xeptiva.com",
    "ycombinator.com","ymmunobio.com","zentynel.com","zoomagri.com",
]

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "pilot", "logos")
os.makedirs(OUT_DIR, exist_ok=True)

ok, skip, fail = 0, 0, 0
for domain in DOMAINS:
    # skip junk
    if any(x in domain for x in ["linkedin", "unknown", "marketing", "crop%20", "lizar.bio%"]):
        skip += 1
        continue
    dest = os.path.join(OUT_DIR, domain + ".png")
    if os.path.exists(dest):
        skip += 1
        continue
    url = f"https://logo.clearbit.com/{domain}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = r.read()
        # Clearbit returns a 1x1 gif or very small image for unknowns — skip those
        if len(data) < 500:
            fail += 1
            continue
        with open(dest, "wb") as f:
            f.write(data)
        ok += 1
        print(f"  ✓ {domain} ({len(data)//1024}KB)")
    except Exception as e:
        fail += 1
        print(f"  ✗ {domain}: {e}")
    time.sleep(0.15)  # ~6 req/s, dentro del free tier

print(f"\nDone: {ok} descargados, {skip} saltados, {fail} sin logo")
