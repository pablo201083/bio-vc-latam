"""One-off: save fund profile blurbs from website research."""
import sqlite3, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from audit import diff_and_log_update

conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', '..', 'db', 'bio_latam.db'))

BLURBS = {
"GridX": (
    "GridX es el vehículo más singular del ecosistema BIO LATAM: opera simultáneamente como aceleradora científica y fondo de capital de riesgo. "
    "Desde 2015 ha completado 9 cohortes, incorporado a más de 250 fundadores y construido un portafolio de +90 startups en 8 países latinoamericanos "
    "bajo la tesis de la \"Life-Based Age\" — la apuesta de que los sistemas vivos reemplazarán a los combustibles fósiles como motor de la economía global."
    "\n\n"
    "Su portafolio refleja la amplitud de esa tesis: Stämm (biomanufactura), Puna Bio (bioinputs), CASPR Biotech (diagnósticos), Beeflow (polinización), "
    "Michroma (pigmentos fúngicos) y OncoPrecision (oncología). Los cuatro vectores — agri-food, bio-industria, salud humana y deep-biotech — le permiten "
    "cubrir verticales que ningún otro fondo regional puede alcanzar con la misma densidad."
    "\n\n"
    "Con $41M AUM y +90 portafolios activos, GridX opera con una relación capital/portafolio muy comprimida: funciona más como hub de construcción de compañías "
    "que como vehículo de capital de crecimiento. Su valor estratégico en el ecosistema es insustituible como generador de deal-flow y validador científico temprano "
    "— pero las startups que escalan deberán buscar capital de seguimiento fuera de su estructura."
),
"sp_ventures": (
    "SP Ventures es el referente regional de AgFood-ClimateTech: más de 10 años de track record, +$100M invertidos en +50 empresas en LATAM. "
    "Su tesis es estructural: la crisis climática y la seguridad alimentaria son el mismo problema visto desde distintos ángulos, y la solución pasa "
    "por reinventar la cadena de valor alimentaria del suelo al estante."
    "\n\n"
    "Como lead investor con tickets hasta $10M en Serie A, cubre el tramo de crecimiento temprano con mayor escasez de capital en el ecosistema. "
    "Sus métricas de impacto son inusuales: 54 millones de hectáreas impactadas y $571M en crédito agrícola facilitado por sus portafolios — "
    "señales de que su capital moviliza recursos mucho mayores que el fondo mismo."
    "\n\n"
    "Empresas como Puna Bio (bioinputs) y Gênica (microbioma del suelo) reflejan su apuesta por la biología como plataforma de solución al problema "
    "agro-climático. Con el track record más sólido del segmento y presencia en toda la región, es uno de los actores con mayor credibilidad para "
    "anclar rondas bio-agro en LATAM."
),
"zentynel": (
    "Zentynel es el primer fondo de capital de riesgo especializado exclusivamente en biotecnología en América Latina, fundado desde la convergencia "
    "inusual de un instituto científico (Fundación Ciencia & Vida) y una gestora de activos alternativos (Venturance). Sus credenciales son excepcionales: "
    "Pablo Valenzuela — co-fundador de Chiron Corporation, adquirida por Novartis en $8.9B — es General Partner. Con sede en Santiago, opera con estándares "
    "de rigor técnico que ningún fondo puramente financiero de la región puede igualar."
    "\n\n"
    "Su tesis \"One Health\" rechaza la fragmentación entre salud humana, animal y ambiental, construyendo un portafolio que refleja esa interconexión: "
    "Momentum Therapeutics y Xeptiva (terapéuticos), Fecundis (agro-diagnósticos), ViewMind (neurociencia), Biomakers (multi-ómicas). "
    "Con 18+ empresas, es el fondo con mayor concentración de ciencia de frontera por capital invertido en el ecosistema regional."
    "\n\n"
    "Lo que distingue a Zentynel no es el ticket sino la capacidad técnica del equipo: un GP con 40 años en biotech tiene una ventaja de selección "
    "científica difícil de replicar en LATAM. Su programa BioGratitud — apoyo a emprendedores fuera del portafolio sin dilución — refleja una filosofía "
    "de construcción de ecosistema más allá del retorno financiero. Es el actor más comprometido con la bioeconomía científica profunda en la región."
),
"kamay_ventures": (
    "Kamay Ventures es el primer fondo multi-corporate de América Latina, respaldado directamente por The Coca-Cola Company, Grupo Arcor y Grupo Bimbo "
    "— tres de las mayores corporaciones de consumo masivo de la región. Esta estructura define su propuesta de valor más allá del capital: las startups "
    "en portafolio acceden a operaciones reales, con más de 69 POCs ejecutados y reach a más de 12 millones de puntos de venta en la región."
    "\n\n"
    "Con tickets Seed/Pre-A de hasta $600K en valuaciones menores a $25M, opera en el segmento más temprano y de mayor riesgo. Sus 21 empresas en "
    "portafolio y presencia activa en 26 países demuestran que el modelo de validación corporativa funciona: las startups reciben capital y tracción "
    "comercial real con clientes de escala global."
    "\n\n"
    "En el mapa BIO LATAM, Kamay es un actor de nicho CPG, pero su conexión con la cadena alimentaria lo hace relevante para startups de foodtech, "
    "agro-supply chain y bio-ingredientes. Para un fundador bio que busca probar mercado a escala, pilotar con Arcor o Coca-Cola en 26 países es una "
    "señal de validación comercial que ningún fondo de venture puede replicar."
),
"the_yield_lab_latam": (
    "The Yield Lab LATAM es el fondo AgriFoodTech con mayor cobertura geográfica de la región: oficinas en Buenos Aires, São Paulo, Rancagua, Medellín "
    "y Ciudad de México desde 2017. Su posición como integradora de ecosistemas — conectando startups, inversores, corporaciones, agricultores y sector "
    "público — es su tesis diferenciadora central. Mapea 70+ categorías de innovación en 12 sectores de la cadena agroalimentaria."
    "\n\n"
    "El foco early-stage y la presencia en cinco países le permite identificar oportunidades que fondos globales no ven — especialmente en la interfaz "
    "suelo-microbioma-alimento que es el núcleo del BIO agri regional. Su equipo multinacional con raíces locales en cada mercado es una ventaja "
    "competitiva que ningún fondo global puede construir en el corto plazo."
    "\n\n"
    "Para el ecosistema BIO, The Yield Lab es uno de los principales generadores de deal-flow en bioinputs, agro-diagnósticos y foodtech. Su limitación "
    "estructural es la ausencia de cobertura growth: las compañías que escalan deberán buscar capital de seguimiento fuera de su red. Pero como buscador "
    "y validador temprano en el agro-bio regional, su red de cinco países es uno de los activos más valiosos del ecosistema."
),
"AIR Capital": (
    "AIR Capital es un fondo de deep tech de tesis amplia: \"innovaciones disruptivas relevantes para la humanidad\". Su portafolio abarca desde space "
    "(Outpost, Skyloom, Aptos Orbital) hasta biotecnología (Stämm, Semion Bio, Dogma Biotech, Oncoliq) y energía — una diversificación que refleja la "
    "apuesta de que el próximo ciclo de innovación será convergente y multidisciplinario."
    "\n\n"
    "Con más de 50 empresas en portafolio, AIR Capital opera con un apetito de riesgo alto y un criterio técnico elevado: Stämm — una de las compañías "
    "más sofisticadas en biomanufactura del hemisferio sur — está en su cartera, lo que indica capacidad real de evaluación científica. El sesgo "
    "argentino es marcado pero sin restricción geográfica explícita."
    "\n\n"
    "En el ecosistema BIO LATAM, AIR es uno de los pocos fondos con capacidad multi-sectorial y vocación de frontera tecnológica. Su falta de "
    "transparencia sobre AUM y estructura de fondo es la principal incógnita sobre su capacidad de follow-on — una variable crítica para startups "
    "bio que planean rondas Series B y posteriores."
),
"The Ganesha Lab": (
    "The Ganesha Lab es una aceleradora de scale-up de life sciences con base en América Latina y proyección global. A diferencia de la mayoría de "
    "los actores del ecosistema, no se presenta como inversor de capital tradicional sino como puente de internacionalización: su propuesta central "
    "es convertir ciencia latinoamericana en negocios con tracción en mercados globales."
    "\n\n"
    "Sus alianzas estratégicas son lo que la distingue: Venture Catalyst (UC Davis), Johnson & Johnson y Life Science Nation le dan acceso a redes "
    "de capital e inversión que la mayoría de las aceleradoras regionales no tiene. La participación en eventos como Deep Tech Summit São Paulo 2025 "
    "y Business Missions internacionales refleja un posicionamiento deliberado en el segmento científico de mayor valor."
    "\n\n"
    "Para el ecosistema BIO, The Ganesha Lab cubre una brecha crítica: la transición de validación científica a empresa comercial con tracción "
    "internacional. Muchas startups bio de la región llegan a resultados prometedores pero carecen del capital relacional para saltar al mercado "
    "global. Ahí es donde Ganesha interviene — no con el cheque más grande, sino con la red correcta en el momento correcto."
),
"SOSV_IndieBio": (
    "SOSV es la organización global detrás de IndieBio, el primer programa de aceleración para biotech con laboratorios físicos integrados. "
    "En 2026, IndieBio fue absorbida bajo la marca SOSV (escindida en SOSV NY y SOSV SF), reflejo de una evolución desde biotech puro hacia "
    "deep tech integral: alimentos, clima, diagnósticos, IA, química y terapéuticos."
    "\n\n"
    "El modelo SOSV es distinto al VC tradicional: invierte en volumen con capital pre-seed, proporciona acceso a laboratorios físicos y co-construye "
    "compañías desde la hipótesis científica. Entre 2015 y 2025, sus graduados levantaron $3.6B en rondas posteriores — una tasa de tracción que "
    "pocos aceleradores globales pueden mostrar."
    "\n\n"
    "Para LATAM, SOSV/IndieBio tiene presencia indirecta pero significativa: varias startups de la región han completado sus programas globales. "
    "Para una startup BIO latinoamericana, entrar a SOSV sigue siendo uno de los saltos de validación más relevantes — no por el capital inicial "
    "sino por la señalización que implica para rondas Serie A y B en mercados de EE.UU. y Europa."
),
"savia_ventures": (
    "Savia Ventures es un fondo de venture capital climático enfocado en América Latina, respaldado por más de 50 líderes corporativos del sector "
    "de sostenibilidad. Invierte en etapas pre-seed y seed en compañías de climatech con operaciones o planes de expansión en LATAM — el momento "
    "de mayor riesgo y mayor potencial de impacto en el ciclo de vida de una startup."
    "\n\n"
    "Sus seis vectores — energía, movilidad, blue economy, agtech/foodtech, climate fintech y manufactura sostenible — reflejan una tesis transversal: "
    "el cambio climático requiere innovación simultánea en toda la economía. Portfolio highlights como Done Properly (ingredientes fúngicos) y "
    "Strong by Form (biocompuestos de madera) muestran su apetito por soluciones bio-industriales de nueva generación."
    "\n\n"
    "Para el ecosistema BIO, Savia es un actor emergente con una tesis alineada con las tendencias de mayor crecimiento global: biomateriales, "
    "bio-insumos climáticos y foodtech alternativo. Su red de 50+ Climate Leaders como LPs y advisors le da acceso a pilotos corporativos y mercados "
    "que pocos fondos climáticos de la región pueden ofrecer a sus portafolios."
),
"newtopia_vc": (
    "Newtopia VC es un fondo early-stage de $50M construido por emprendedores detrás de unicornios latinoamericanos. Su red de co-inversores incluye "
    "a Marcos Galperin (Mercado Libre) y otros fundadores referentes de la región — lo que convierte a Newtopia en una señal de validación de primer "
    "nivel para startups que buscan acceso al ecosistema tech de mayor escala."
    "\n\n"
    "Su modelo \"entrepreneurs supporting entrepreneurs\" apuesta a que el mejor capital para etapas tempranas viene de quienes ya recorrieron el camino. "
    "Con tickets hasta $1.5M en seguimiento de Serie A, cubre el espectro pre-seed a Serie A con una propuesta de acompañamiento operativo intensivo."
    "\n\n"
    "En el ecosistema BIO, Newtopia es un actor generalista — su portafolio visible (Auth0, Mural, Tiendanube, Satellogic) no muestra concentración bio. "
    "Para una startup BIO, el valor de Newtopia no es la especialización sectorial sino la red: entrar a su portafolio abre puertas a una comunidad "
    "de unicornios y co-inversores que puede acelerar significativamente las rondas posteriores."
),
"kaszek": (
    "Kaszek es el fondo de venture capital más influyente de América Latina: fundado por Hernán Kazah y Nicolás Szekasy — ex-Vicepresidente y CFO de "
    "MercadoLibre respectivamente — con 9 fondos bajo gestión y 130 ventures respaldados en 20 años de historia regional. Combina Early Funds (Seed a "
    "Serie B) con Opportunity Funds (Serie C a pre-IPO), siendo uno de los pocos actores regionales con capacidad de growth capital real."
    "\n\n"
    "Su tesis es tecnológica y horizontal: fintech, healthtech, edtech, e-commerce, enterprise SaaS — cualquier sector donde la tecnología pueda crear "
    "disrupciones significativas. No tiene un mandato bio específico, pero su presencia en healthtech y su posición como árbitro del ecosistema lo "
    "convierte en puerta de entrada para startups bio que buscan validación de mercado tech."
    "\n\n"
    "Para el ecosistema BIO, Kaszek es estratégico no por su inversión directa en biotech sino por su rol de legitimación: cuando Kaszek co-invierte "
    "o sigue una ronda bio, el resto del ecosistema regional e internacional lo lee como señal de calidad. Con oficinas en Buenos Aires, México, "
    "Montevideo y São Paulo, es el vehículo con la red de capital más densa de la región."
),
"vox_capital": (
    "Vox Capital es la gestora de impacto más consolidada de Brasil: pionera del impact investing en el país, con estrategias de VC (Tech for Good), "
    "crédito privado estructurado y gestión de portafolios de impacto para familias y fundaciones. Su tesis central: toda inversión tiene impacto — "
    "la diferencia está en si ese impacto es positivo o negativo."
    "\n\n"
    "Sus cuatro pilares de decisión — riesgo, retorno, liquidez e impacto — la diferencian de los fondos ESG tradicionales que suman el impacto como "
    "capa adicional. En bioeconomía específicamente, Vox identifica el sector como uno de los vectores estratégicos para Brasil, junto con inclusión "
    "financiera y transición climática."
    "\n\n"
    "Para el ecosistema BIO LATAM, Vox Capital es un actor de puente: no es un fondo biotech, pero su mandato de impacto positivo y su alineación "
    "con bioeconomía la convierte en un potencial inversor para startups bio que demuestren métricas de impacto claras. Su posición como creador "
    "del primer fondo de renta fija de impacto de Brasil sugiere capacidad para estructurar instrumentos financieros no convencionales."
),
"Antom": (
    "Antom es un fondo de impacto pre-seed y seed para proyectos regenerativos en América Latina. Su mandato es explícitamente ambiental: las métricas "
    "de decisión incluyen reducción de CO2, captura de GEI, aumento de biodiversidad y reducción de residuos. Opera con tickets de $25K a $100K vía "
    "contratos SAFE, o mediante Revenue Share (5% de ventas mensuales durante 7 años, cap en 4x) — una estructura que reduce la dilución para "
    "fundadores en etapas muy tempranas."
    "\n\n"
    "Su foco abarca climatech, agri-foodtech agroecológico, economía circular y eficiencia energética. La combinación de equity y Revenue Share como "
    "instrumentos complementarios es una señal de adaptabilidad a los flujos de caja de startups en mercados emergentes donde el modelo estándar "
    "de VC puede no ser óptimo."
    "\n\n"
    "Para el ecosistema BIO, Antom es un actor de nicho early pero relevante: su mandato regenerativo y su enfoque agroecológico lo conectan con "
    "bioinputs, biomateriales y foodtech alternativo. Con tickets pequeños pero procesos ágiles y criterios de impacto claros, puede ser el primer "
    "cheque institucional para startups bio-ambientales que aún no alcanzan el radar de fondos de mayor escala."
),
"CITES": (
    "CITES (Centro de Innovación Tecnológica, Empresarial y Social) es un fondo de deep science con sede en Argentina — con presencia en Sunchales "
    "(Santa Fe), Buenos Aires y Bariloche — especializado en transformar ciencia disruptiva en negocios. Su tesis: las tecnologías que parecen "
    "imposibles hoy serán transformadoras mañana. Con 95+ patentes bajo gestión y 250+ científicos vinculados, opera como puente entre la academia "
    "argentina y el mercado."
    "\n\n"
    "Su infraestructura física es su diferencial: fab-labs, wet-labs y espacios de co-creación integrados con el capital. Esto le permite invertir "
    "desde la idea ($25K) hasta Serie A ($3.5M), cubriendo el valle de la muerte tecnológico que elimina a la mayoría de los proyectos de deep science "
    "antes de alcanzar el mercado. Con 23 empresas en portafolio, concentra la mayor densidad de deeptech científico por capital invertido en Argentina."
    "\n\n"
    "En el ecosistema BIO LATAM, CITES cumple una función crítica de infraestructura: no solo invierte sino que habilita físicamente la creación de "
    "startups biotech y agtech desde la investigación básica. Su presencia en Sunchales — epicentro del agro-industrial santafesino — lo conecta "
    "directamente con el ecosistema de bioinputs y agrobiotech del Litoral argentino, uno de los clusters más relevantes del cono sur."
),
}

ok = 0
for investor_id, blurb in BLURBS.items():
    try:
        diff_and_log_update(
            conn, table="investors", row_id_col="investor_id", row_id=investor_id,
            new_values={"profile_blurb": blurb},
            actor="pablo202083",
            reason="Perfil generado desde contenido de website oficial del fondo",
        )
        ok += 1
        print(f"OK: {investor_id}")
    except Exception as e:
        print(f"ERROR {investor_id}: {e}")

conn.commit()
print(f"\nTotal guardados: {ok}/{len(BLURBS)}")
