# BIO VC LATAM cleanup queue

Objetivo: cerrar el universo de startups BIO VC LATAM y su red de capital con menos ambiguedad posible.

## Foto de trabajo

- Exclude provisional a revisar por falsos negativos: 63
- Include sin pais/base claro: 58
- Include fragile: 6

## Orden recomendado

1. Revisar exclude provisional con mayor senal BIO/capital.
2. Completar founding/base country para include confirmadas.
3. Endurecer las include fragile.
4. Regenerar base, dashboards y export capital.

## Top exclude provisional a revisar

- Lemon | priority 3 | capital=True | peripheral or non-core digital ventures
- Spectrum | priority 3 | capital=True | peripheral or non-core digital ventures
- Invitrall | priority 2 | capital=True | peripheral or underclassified ventures
- Lipock | priority 2 | capital=True | peripheral or underclassified ventures
- TravelX | priority 2 | capital=True | peripheral or non-core digital ventures
- Vu | priority 2 | capital=False | peripheral or non-core digital ventures
- Zipnova | priority 2 | capital=True | peripheral or non-core digital ventures
- Fligoo | priority 1 | capital=False | peripheral or non-core digital ventures
- Frete Com | priority 1 | capital=False | peripheral or non-core digital ventures
- Iof | priority 1 | capital=False | peripheral or underclassified ventures
- Logan | priority 1 | capital=False | peripheral or non-core digital ventures
- Luzid | priority 1 | capital=False | peripheral or non-core digital ventures
- Menta Tickets | priority 1 | capital=False | peripheral or non-core digital ventures
- Nuclearis | priority 1 | capital=False | frontier hardware and infrastructure systems
- Nuvia | priority 1 | capital=False | frontier hardware and infrastructure systems


## Top include sin pais/base

- Caligenia | priority 12 | source=https://www.gridexponential.com/portfolio
- Syocin Biotech | priority 11 | source=https://syocin.com/
- APEXzymes | priority 10 | source=https://apexzymes.com/
- Food4You | priority 10 | source=https://www.gridexponential.com/portfolio
- SoyGREEN | priority 10 | source=https://soygreen.com.ar
- Arqlite | priority 9 | source=https://curbwaste.com/company-profiles-network/arqlite
- BioBlends | priority 9 | source=https://cancilleria.gob.ar/en/new-technologies/next-form-argentine/bioblends
- Bioheuris | priority 9 | source=https://bioheuris.com/aboutus
- Enzyva | priority 9 | source=https://www.enzyvo.com/about
- Fecundis | priority 9 | source=https://www.fecundis.com/
- Ruuts | priority 9 | source=https://ruuts.la/
- ArgenTAG | priority 8 | source=https://sosv.com/company/argentag/
- BEAM CropTech | priority 8 | source=https://beamcroptech.com/en/home-en/
- Biotalife | priority 8 | source=https://www.biotalife.com/
- Bitgenia | priority 8 | source=https://www.bitgenia.com/nosotros/


## Include fragile

- Aquit | missing=missing_country; thin_graph_context | source=https://www.f6s.com/company/aquit
- Food4You | missing=missing_country; missing_trl; thin_graph_context; unclassified_sector | source=https://www.gridexponential.com/portfolio
- Elytron Biotech | missing=missing_country; missing_trl; unclassified_sector | source=https://www.elytronbiotech.com/?lang=en
- Plamic Biotech | missing=missing_country; missing_trl; thin_graph_context; unclassified_sector | source=https://www.argentina.gob.ar/noticias/se-conocieron-los-ganadores-del-concurso-innova-salud
- Agree | missing=missing_country; thin_graph_context | source=https://theyieldlablatam.com/companies/agree/
- Laurus AG Tech | missing=missing_country; missing_trl; thin_graph_context; unclassified_sector | source=https://www.f6s.com/company/laurusagtech

