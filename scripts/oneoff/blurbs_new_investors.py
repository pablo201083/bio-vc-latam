"""Saves profile blurbs for newly added investors."""
import sys, os, sqlite3
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from audit import diff_and_log_update

DB = os.path.join(os.path.dirname(__file__), '..', '..', 'db', 'bio_latam.db')
conn = sqlite3.connect(DB)

BLURBS = {
    "mov_investimentos": (
        "MOV Investimentos es una gestora de impacto fundada en 2012 en Sao Paulo con certificacion B Corp. "
        "Su tesis central es invertir en emprendedores que reducen desigualdad social y degradacion ambiental "
        "en Brasil y America Latina, con foco especial en bioeconomia, agbio y biofarmaceutica.\n\n"
        "En su Fund II, MOV concentra capital en soluciones de bosques, agricultura regenerativa y bioeconomia. "
        "Es co-inversor en Symbiomics (biologicos para cultivos con microbioma y edicion genomica) y en Nintx "
        "(terapias biologicas targeting microbioma intestinal), lo que lo ubica como uno de los pocos fondos "
        "brasileros con presencia simultanea en agbio y biofarmaceutica.\n\n"
        "Para el ecosistema BIO LATAM, MOV es un actor puente entre capital de impacto y biotech de frontera. "
        "Su presencia en deals junto a Corteva Catalyst (Symbiomics) senaliza validacion estrategica: cuando "
        "MOV entra, suele traer consigo acceso a redes de distribucion agroindustrial y visibilidad institucional."
    ),
    "vesper_ventures": (
        "Vesper Ventures es un fondo de tipo venture builder fundado en Florianopolis, Brasil. "
        "A diferencia de un VC convencional, Vesper co-crea las startups desde cero, reuniendo "
        "cientificos y emprendedores para construir plataformas tecnologicas en terapeutica, "
        "diagnostico, produccion de alimentos y medioambiente.\n\n"
        "Su modelo de co-fundacion le da participacion accionaria alta y alineacion a largo plazo "
        "con las empresas de su portafolio. Entre sus inversiones: Symbiomics (biologicos agricolas), "
        "Cellertz Bio, InEdita Bio (edicion genomica), Hapiseeds y Reddot Bio. "
        "Figura consistentemente en los tres principales fondos brasileros de biotech junto a GRIDS Capital y LifelyVC.\n\n"
        "En el contexto BIO LATAM, Vesper es un nodo de origen: muchas de las biotech brasileras mas prometedoras "
        "nacieron o pasaron por su estructura. Su presencia en el cap table de una startup suele indicar "
        "fundamentos cientificos solidos desde etapa pre-comercial."
    ),
    "ecoa_capital": (
        "Ecoa Capital es una gestora brasilera fundada en 2021 en Sao Paulo que invierte en "
        "deep tech con foco en drug discovery, agbiotech y biologia sintetica. "
        "Con 17 inversiones documentadas, su portafolio incluye Symbiomics, Nintx e InEdita Bio, "
        "lo que la posiciona como uno de los fondos mas activos en biotech temprano en Brasil.\n\n"
        "Su tesis articula tecnologia y impacto: busca companaias que resuelvan problemas de "
        "desigualdad social o degradacion ambiental mediante innovacion profunda. "
        "La presencia de Ecoa junto a Vesper Ventures y MOV Investimentos en Symbiomics ilustra "
        "el cluster emergente de capital biotech en el Sur de Brasil.\n\n"
        "Para inversores de etapas posteriores, Ecoa funciona como senalizador de calidad tecnica: "
        "su due diligence en ciencias de la vida es riguroso y su red de conexiones con laboratorios "
        "universitarios brasileros es una ventaja diferencial."
    ),
    "green_rock": (
        "Green Rock es un fondo de venture capital brasilero con foco en deep-tech y healthtech. "
        "Es el inversor principal documentado en Brain4care, la startup de Sao Carlos que desarrolla "
        "monitoreo no invasivo de compliance intracraneal, reconocida como pionera global de tecnologia "
        "2025 por el Foro Economico Mundial.\n\n"
        "El fondo opera con un perfil de riesgo alto y apetito por ciencia frontier: "
        "neurotecnologia, medtech con innovacion de plataforma y salud digital con componente IP "
        "defensible son sus areas de mayor actividad.\n\n"
        "En el ecosistema BIO LATAM, Green Rock es representativo de una segunda generacion de fondos "
        "brasileros dispuestos a apostar por biotech con ciclos de desarrollo largos, algo excepcional "
        "en un mercado donde predominan inversores de healthtech digital y software de salud."
    ),
    "general_catalyst": (
        "General Catalyst es uno de los principales fondos de venture capital de Estados Unidos, "
        "con sede en Cambridge y mas de $6B en activos bajo administracion. "
        "En LATAM tiene presencia creciente en health-tech: lidera la Serie A de Examedi (Chile) "
        "y de Genial Care (Brasil), posicionandose como el VC gringo de mayor conviction en "
        "plataformas de salud a domicilio y salud pediatrica especializadaen la region.\n\n"
        "Su estrategia es buscar companaias con modelo de distribucion escalable en mercados "
        "subatendidos. Examedi (diagnosticos a domicilio, 12 paises LATAM) y Genial Care "
        "(atencion multidisciplinaria para ninos con autismo) encajan en este patron: "
        "mercados grandes, penetracion baja, unidad economica validada.\n\n"
        "Para fundadores LATAM, conseguir a General Catalyst como lead es una senial de clase mundial: "
        "abre puertas a rondas series siguientes con fondos tier-1 de Silicon Valley y "
        "confiere legitimidad internacional que facilita expansion a nuevos mercados."
    ),
    "y_combinator": (
        "Y Combinator es el acelerador de startups mas influyente del mundo, con sede en "
        "San Francisco. Invierte $500K por 7% en las companias de cada batch y ofrece "
        "acceso a una red de mas de 4,000 alumni que incluye Airbnb, Stripe y DoorDash.\n\n"
        "En LATAM biotech/health, YC ha respaldado companaias como Examedi (Chile), demostrando "
        "apertura creciente a fundadores latinoamericanos con modelos de salud accesible. "
        "El sello YC es una de las seniales de credibilidad mas fuertes en el mercado global: "
        "facilita rondas subsiguientes con fondos tier-1 como General Catalyst, Sequoia o a16z.\n\n"
        "Su presencia en el ecosistema BIO LATAM es aun limitada pero estrategica: cada startup "
        "LATAM que pasa por YC amplia el mapa de lo que el fondo considera fundadores financiables, "
        "creando un efecto de red positivo para la proxima generacion de fundadores de la region."
    ),
}

for investor_id, blurb in BLURBS.items():
    r = conn.execute("SELECT investor_id FROM investors WHERE investor_id=?", (investor_id,)).fetchone()
    if not r:
        print(f"SKIP {investor_id} - not in investors table")
        continue
    diff_and_log_update(
        conn, "investors", "investor_id", investor_id,
        {"profile_blurb": blurb},
        actor="blurbs_new_investors",
        reason="Profile blurb from fund research sprint Q2 2026"
    )
    print(f"  blurb saved: {investor_id}")

conn.commit()
conn.close()
print("Done.")
