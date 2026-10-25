"""Generate *simulated* AUD prices for a PC Builder teaching/demo catalogue.

Input: MySQL Workbench-exported file with columns component_id, category,
manufacturer, model, release_date, specifications. Supports this specific
Workbench CSV quirk where embedded JSON quotes were not doubled.

Outputs: price_seed_review.csv, price_seed_apply.sql, price_seed_summary.txt.
Does NOT connect to a database, invoke an LLM, or verify current offers.
"""
from __future__ import annotations
import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path

GENERATED_AT = '2026-10-25'
METHOD = 'ai_assisted_rule_based_demo_v1'

# Baselines are indicative demonstration values in AUD, NOT researched offers
# for the individual products. Refer to PRICE_METHODOLOGY.md for limitations.
GPU_BASE = {
 'GTX 1080 Ti':260, 'GTX 1650':140, 'GTX 1650 SUPER':160,
 'GTX 1660':170, 'GTX 1660 SUPER':190, 'GTX 1660 Ti':185,
 'RTX 2060':180, 'RTX 2060 SUPER':225, 'RTX 2070':230,
 'RTX 2070 SUPER':270, 'RTX 2080':285, 'RTX 2080 SUPER':325, 'RTX 2080 Ti':380,
 'RTX 3050':255, 'RTX 3060':295, 'RTX 3060 Ti':340, 'RTX 3070':395,
 'RTX 3070 Ti':460, 'RTX 3080':570, 'RTX 3080 Ti':670,
 'RTX 3090':890, 'RTX 3090 Ti':1050,
 'RTX 4060':430, 'RTX 4060 Ti':580, 'RTX 4070':735, 'RTX 4070 SUPER':845,
 'RTX 4070 Ti':940, 'RTX 4070 Ti SUPER':1130,
 'RTX 4080':1390, 'RTX 4080 SUPER':1450, 'RTX 4090':2950,
 'RTX 5050':410, 'RTX 5060':570, 'RTX 5060 Ti':735,
 'RTX 5070':995, 'RTX 5070 Ti':1350, 'RTX 5080':2390, 'RTX 5090':5950,
 'RX 5500 XT':155, 'RX 5600 XT':195, 'RX 5700':240, 'RX 5700 XT':270,
 'RX 6400':150, 'RX 6500 XT':195, 'RX 6600':250, 'RX 6600 XT':300,
 'RX 6650 XT':320, 'RX 6700':355, 'RX 6700 XT':395, 'RX 6750 XT':435,
 'RX 6800':525, 'RX 6800 XT':600, 'RX 6900 XT':700, 'RX 6950 XT':780,
 'RX 7600':360, 'RX 7600 XT':440, 'RX 7700 XT':545, 'RX 7800 XT':690,
 'RX 7900 GRE':750, 'RX 7900 XT':900, 'RX 7900 XTX':1170,
 'RX 9060':530, 'RX 9060 XT':630, 'RX 9070 GRE':805,
 'RX 9070':795, 'RX 9070 XT':970,
 'RTX 4500 Ada':3700, 'RTX 5000 Ada':6500, 'RTX 5880 Ada':7700,
}
# Match longest first (Ti/SUPER/XT variants before parent SKUs).
GPU_KEYS = sorted(GPU_BASE, key=len, reverse=True)

CPU_SPECIFIC = {
 'RYZEN 5 5500':135, 'RYZEN 5 5600':190, 'RYZEN 5 5600X':235,
 'RYZEN 5 7500F':245, 'RYZEN 5 7600X':330, 'RYZEN 5 9600X':355,
 'RYZEN 7 5700X':265, 'RYZEN 7 5800X':270,
 'RYZEN 7 5700X3D':350, 'RYZEN 7 7800X3D':500,
 'RYZEN 7 9800X3D':600, 'RYZEN 9 9900X':630, 'RYZEN 9 9950X3D':940,
 'CORE ULTRA 5 245K':290, 'CORE ULTRA 7 265K':410,
 'CORE I5 14400F':250,
}

CATEGORY_BOUNDS = {
 'CPU':(75,2400), 'GPU':(80,14000), 'Motherboard':(65,1600),
 'RAM':(30,7000), 'Storage':(35,4000), 'PSU':(50,1800),
}


def parse_rows(path: Path):
    rows=[]
    lines=path.read_text(encoding='utf-8-sig').splitlines()
    required='component_id,category,manufacturer,model,release_date,specifications'
    if not lines or lines[0].strip()!=required:
        raise ValueError('Unexpected CSV header; inspect input before continuing.')
    seen=set()
    for row_number,line in enumerate(lines[1:],start=2):
        # The supplied Workbench export wraps JSON in quotes without escaping
        # its internal quote characters. Parse the first 4 fields independently
        # and decode the original literal JSON instead of using csv.DictReader.
        # All rows in this export have a NULL release_date.
        if ',NULL,"' not in line or not line.endswith('"'):
            raise ValueError(f'Unexpected date/JSON layout on row {row_number}')
        prefix,json_part=line.split(',NULL,"',1)
        fields=next(csv.reader([prefix]))
        if len(fields)!=4:
            raise ValueError(f'Invalid identity fields on row {row_number}')
        cid,category,manufacturer,model=fields
        cid=int(cid)
        if cid in seen: raise ValueError(f'Duplicate component ID {cid}')
        seen.add(cid)
        spec=json.loads(json_part[:-1])
        if not isinstance(spec,dict):raise ValueError('Specifications must be a JSON object')
        rows.append(dict(component_id=cid,category=category,manufacturer=manufacturer,model=model,specifications=spec))
    return rows


def num(value,default=0):
    try: return float(value)
    except (TypeError,ValueError): return default


def fmt_price(value):
    return int(round(max(value,1)/5)*5)


def estimate_cpu(r):
    name=r['model'].upper(); spec=r['specifications']
    year=int(spec.get('release_year') or 0); cores=num(spec.get('cores'),6)
    if 'RYZEN' in name:
        series=re.search(r'RYZEN\s+([3579])',name)
        tier=int(series.group(1)) if series else 5
        gen=re.search(r'\b([5798])\d{3}[A-Z0-9]*\b',name)
        g=int(gen.group(1)) if gen else (9 if year>=2024 else 7)
        bases={5:{5:210,7:295,8:275,9:340},7:{5:300,7:400,8:360,9:430},9:{5:440,7:580,8:540,9:750}}
        b=bases.get(tier,bases[5]).get(g,250)
        b*=1+min(max(0,cores-6)*0.015,0.15)
        if 'X3D' in name: b+=125 if tier<=7 else 185
        if re.search(r'\bG\b|\dG\b|GT\b',name): b*=0.87
        if 'OEM' in name or 'TRAY' in name:b*=0.92
    elif 'CORE' in name:
        tier_match=re.search(r'(?:CORE\s+I|CORE\s+ULTRA\s+)([3579])',name)
        tier=int(tier_match.group(1)) if tier_match else 5
        b={3:150,5:280,7:450,9:720}.get(tier,280)
        if 'ULTRA' in name: b*=1.15
        elif '12' in name: b*=0.78
        elif '13' in name: b*=0.92
        elif '14' in name: b*=1.03
        if re.search(r'\b\d{4,5}K',name):b*=1.12
        if re.search(r'\b\d{4,5}KS',name):b*=1.10
        if re.search(r'\b\d{4,5}[FT]\b',name):b*=0.90
        if 'PLUS' in name:b*=1.12
        if 'OEM' in name or 'TRAY' in name:b*=0.9
    else:
        return 320,'low','CPU family not matched; generic processor estimate'
    for specific,ref in sorted(CPU_SPECIFIC.items(),key=lambda item:len(item[0]),reverse=True):
        # Match exact SKU, optionally with packaging postfix, avoiding 5600X/5600GT matching 5600.
        if re.search(r'\b'+re.escape(specific)+r'(?![A-Z0-9])',name):
            return ref,'medium',f'CPU reference family / SKU: {specific}'
    return b,'medium',f'CPU family/tier/core-count estimate; release year {year}'


def estimate_gpu(r):
    name=r['model'].upper(); spec=r['specifications']
    chipset=str(spec.get('chipset') or name).upper()
    chipset=chipset.replace('GEFORCE ','').replace('RADEON ','').replace('NVIDIA ','').replace('AMD ','')
    # Workstation Ada variants do not have gaming benchmark parity.
    b=None;key=None
    for k in GPU_KEYS:
        if k.upper() in chipset:
            key=k;b=GPU_BASE[k];break
    if b is None:
        return 700,'low','Unrecognised GPU chipset; generic demonstration value'
    if key=='RTX 5060 Ti': b=745 if num(spec.get('vram_gb'))>=16 else 605
    if key=='RX 9060 XT':b=730 if num(spec.get('vram_gb'))>=16 else 590
    if key=='RTX 4060 Ti': b=615 if num(spec.get('vram_gb'))>=16 else 530
    if key=='RTX 3050': b=210 if num(spec.get('vram_gb'))<=6 else 265
    if key=='RTX 3060': b=270 if num(spec.get('vram_gb'))<=8 else 300
    if key=='RTX 3080': b=620 if num(spec.get('vram_gb'))>=12 else 565
    premium=0
    if any(v in name for v in ['ROG STRIX','AORUS MASTER','SUPRIM','LIQUID','WATERFORCE','NITRO+','RED DEVIL','ASTRAL']):premium=0.13
    elif any(v in name for v in ['GAMING X','GAMING OC','TUF','NITRO','MERC','FTW3','PHANTOM GAMING','AERO OC']):premium=0.06
    if premium and key.startswith(('GTX ','RTX 20','RTX 30','RX 5','RX 6')):premium*=0.5
    b*=1+premium
    return b,'medium',f'GPU chipset {key}; variant adjustment {premium:.0%}'


def estimate_mobo(r):
    s=r['specifications'];name=r['model'].upper(); chip=str(s.get('chipset') or name).upper()
    match=re.search(r'(X870E|X870|X670E|X670|X570|X470|B850|B650E|B650|B550|B450|B860|B760|B660|H870|H770|H670|H610|H510|A620|A520|A320|Z890|Z790|Z690|Z590|W790|TRX50|X399|B840|A820)',chip+' '+name)
    key=match.group(1) if match else None
    base={
    'A320':90,'A520':110,'A620':140,'A820':155,'B450':130,'B550':165,'B650':220,'B650E':300,'B850':275,'B840':160,
    'X470':210,'X570':270,'X670':385,'X670E':470,'X870':425,'X870E':550,
    'H510':110,'H610':135,'H670':190,'H770':205,'H870':245,
    'B660':170,'B760':205,'B860':255,'Z590':240,'Z690':285,'Z790':340,'Z890':380,
    'W790':1050,'TRX50':920,'X399':550,
    }.get(key,215)
    if 'WIFI' in name or 'WI-FI' in name or 'WIFI' in str(s.get('opendb_data',{})).upper()[:220]:base+=22
    ff=str(s.get('form_factor') or '').upper()
    if 'E-ATX' in ff:base*=1.13
    if 'MINI-ITX' in ff or 'MINI ITX' in name:base*=1.15
    if any(w in name for w in ['ROG MAXIMUS','ROG CROSSHAIR','MEG GODLIKE','AORUS XTREME']):base*=2
    elif any(w in name for w in ['ROG STRIX','AORUS MASTER','ACE','TAICHI','CREATOR']):base*=1.33
    if 'DDR4' in name and key in ('B760','B660','Z690','Z790'):base*=0.92
    return base, 'medium' if key else 'low',f'Motherboard chipset {key or "unknown"}; features and form factor'


def estimate_ram(r):
    s=r['specifications']; name=r['model'].upper()
    size=num(s.get('capacity_gb') or s.get('capacity'),32)
    if not (0<size<=512):return 550,'low','Missing or implausible RAM capacity'
    ddr=str(s.get('ram_type') or s.get('type') or '').upper()
    speed=num(s.get('speed'),3200)
    if 'DDR5' in ddr:
        base=660*(size/32)**0.85
        base*=1+min(max(speed-5600,0)/20000,0.20)
    elif 'DDR4' in ddr:
        base=150*(size/32)**0.85
        base*=1+min(max(speed-3200,0)/18000,0.12)
    else: return 360*(size/32)**.8,'low','RAM generation missing'
    if 'ECC' in name or 'REGISTERED' in name:base*=1.25
    if 'RGB' in name:base*=1.08
    if any(q in name for q in ['TRIDENT Z','DOMINATOR','PLATINUM','XTREEM','PREDATOR']):base*=1.13
    return base,'medium',f'{ddr}, {size:g} GB, {speed:g} MT/s + product features'


def estimate_storage(r):
    s=r['specifications']; name=r['model'].upper()
    gb=num(s.get('capacity_gb'),1000)
    if not 30<=gb<=40000:return 150,'low','Storage capacity missing/outside accepted range'
    iface=str(s.get('interface','')).upper()
    if '5.0' in iface or 'GEN5' in name or 'PCIE 5' in name:gen=5
    elif '4.0' in iface or 'GEN4' in name or 'PCIE 4' in name:gen=4
    elif '3.0' in iface or 'GEN3' in name:gen=3
    else:gen=0
    base={5:210,4:155,3:135,0:130}[gen]*(gb/1000)**0.90
    if any(v in name for v in ['990 PRO','980 PRO','SN850X','T705','FURY RENEGADE','FIRECUDA','KC3000']):base*=1.30
    if 'HEATSINK' in name:base*=1.07
    if str(s.get('storage_type','')).upper()=='HDD':base*=.58
    return base,'medium' if gen else 'low',f'{gb:g} GB storage, PCIe generation {gen or "not specified"}'


def estimate_psu(r):
    s=r['specifications']; name=r['model'].upper()
    watts=num(s.get('wattage_w') or re.sub(r'[^0-9.]','',str(s.get('wattage',750))),750)
    if not 250<=watts<=2500:return 170,'low','PSU wattage missing/outside accepted range'
    base=85+max(0,watts-500)*.12
    rating=str(s.get('efficiency_rating','')).upper()
    if 'TITANIUM' in rating:base*=1.7
    elif 'PLATINUM' in rating:base*=1.34
    elif 'GOLD' in rating:base*=1.12
    elif 'BRONZE' in rating:base*=.93
    elif 'WHITE' in rating:base*=.83
    modular=str(s.get('modular','')).upper()
    if modular=='FULL':base*=1.10
    elif modular=='SEMI':base*=1.05
    if any(a in name for a in ['ROG','DARK POWER','PRIME TX','VERTEX','HYDRO TI']):base*=1.23
    return base,'medium',f'{watts:g} W, {rating or "unrated"}, {modular or "unknown"} modularity'

ESTIMATORS={'CPU':estimate_cpu,'GPU':estimate_gpu,'Motherboard':estimate_mobo,'RAM':estimate_ram,'Storage':estimate_storage,'PSU':estimate_psu}

def build_estimate(r):
    cat=r['category'];spec=r['specifications'];name=r['model']
    issues=[]
    if cat not in ESTIMATORS:raise ValueError(f'Unexpected category: {cat}')
    year=spec.get('release_year')
    if year is None:issues.append('release_year_missing')
    elif not isinstance(year,int) or not 2017<=year<=2026:issues.append('release_year_unexpected')
    if 'RYZEN' in name.upper() and str(spec.get('socket','')).upper()=='AM5' and year is not None and year<2022:
        issues.append('release_year_socket_conflict')
    if 'CORE ULTRA' in name.upper() and year is not None and year<2024:issues.append('release_year_model_conflict')
    if cat=='GPU' and not spec.get('chipset'):issues.append('gpu_chipset_missing')
    raw,confidence,basis=ESTIMATORS[cat](r)
    lo,hi=CATEGORY_BOUNDS[cat]
    price=fmt_price(min(max(raw,lo),hi))
    if price in (lo,hi):issues.append('estimate_clipped_to_bounds')
    if cat=='CPU' and ('OEM' in name.upper() or 'TRAY' in name.upper()):issues.append('oem_tray_cpu')
    if cat=='GPU' and year is not None and year<=2020:issues.append('older_gpu_assumed_used_market')
    if cat=='GPU' and (' ADA' in name.upper() or 'GENERATION' in name.upper()):issues.append('workstation_gpu_not_gaming')
    if cat=='RAM' and num(spec.get('capacity_gb') or spec.get('capacity'))>128:issues.append('high_capacity_ram_price_uncertain')
    if confidence=='low':issues.append('low_confidence_estimation')
    return dict(
       component_id=r['component_id'], category=cat, manufacturer=r['manufacturer'],
       model=name, release_year=year or '', estimated_price_aud=f'{price:.2f}',
       price_type='synthetic_estimate', currency='AUD',confidence=confidence,
       estimation_basis=basis, validation_flags='; '.join(issues),
       opendb_source_url=(spec.get('source') or {}).get('url',''),
    )


def make_files(input_file:Path, outdir:Path):
    rows=parse_rows(input_file)
    output=[build_estimate(r) for r in rows]
    outdir.mkdir(parents=True,exist_ok=True)
    fieldnames=['component_id','category','manufacturer','model','release_year','estimated_price_aud','price_type','currency','confidence','estimation_basis','validation_flags','opendb_source_url']
    with (outdir/'price_seed_review.csv').open('w',encoding='utf-8-sig',newline='') as fh:
        w=csv.DictWriter(fh,fieldnames=fieldnames);w.writeheader();w.writerows(output)
    sql_path=outdir/'price_seed_review_then_apply.sql'
    with sql_path.open('w',encoding='utf-8') as fh:
        fh.write("-- PHASE 5 PC BUILDER: SIMULATED DEMO PRICE SEED. NOT RETAIL QUOTES.\n")
        fh.write("-- Back up pc_building_system before executing. Review price_seed_review.csv first.\n")
        fh.write("-- Safe: updates ONLY rows with price IS NULL, retaining original IDs and other fields.\n")
        fh.write("-- Adds transparent metadata within existing JSON specifications.\n")
        fh.write("USE `pc_building_system`;\nSTART TRANSACTION;\n")
        for row in output:
            id_=int(row['component_id']);price=row['estimated_price_aud'];confidence=row['confidence']
            esc=lambda v: str(v).replace('\\','\\\\').replace("'", "''")
            cat=esc(row['category']);mfg=esc(row['manufacturer']);model=esc(row['model'])
            fh.write(f"UPDATE `component` SET `price` = {price}, `specifications` = JSON_SET(COALESCE(`specifications`, JSON_OBJECT()), '$.price_metadata', JSON_OBJECT('type','synthetic_estimate','currency','AUD','estimated_at','{GENERATED_AT}','method','{METHOD}','confidence','{confidence}')) WHERE `component_id` = {id_} AND `category` = '{cat}' AND `manufacturer` = '{mfg}' AND `model` = '{model}' AND `price` IS NULL;\n")
        fh.write("SELECT COUNT(*) AS remaining_missing_prices FROM `component` WHERE `price` IS NULL;\n")
        fh.write("SELECT JSON_UNQUOTE(JSON_EXTRACT(`specifications`, '$.price_metadata.type')) AS price_type, COUNT(*) AS count FROM `component` GROUP BY price_type;\n")
        fh.write("-- SAFETY DEFAULT: this script rolls back. After independent review and backup,\n")
        fh.write("-- change this last ROLLBACK to COMMIT to make updates permanent.\nROLLBACK;\n")
    with (outdir/'validation_flags_review.csv').open('w',encoding='utf-8-sig',newline='') as fh:
        w=csv.DictWriter(fh,fieldnames=fieldnames);w.writeheader()
        w.writerows(row for row in output if row['validation_flags'])
    stats=Counter(r['category'] for r in output)
    price_stats={cat:[float(r['estimated_price_aud']) for r in output if r['category']==cat] for cat in stats}
    issues=Counter(f for r in output for f in (r['validation_flags'].split('; ') if r['validation_flags'] else []))
    missing_spec=Counter()
    for r in rows:
        if not r['specifications'].get('source'):missing_spec[r['category']]+=1
    with (outdir/'price_seed_summary.txt').open('w',encoding='utf-8') as fh:
        fh.write(f'Generated: {GENERATED_AT}\nInput rows recovered: {len(rows)}\n')
        fh.write('IMPORTANT: these prices are synthetic/estimated for demonstration, NOT verified live offers.\n\n')
        fh.write('CATEGORY ESTIMATES (AUD)\n')
        for cat in ('CPU','GPU','Motherboard','RAM','Storage','PSU'):
            d=sorted(price_stats[cat]);fh.write(f'{cat:<15} {len(d):>5}  minimum ${d[0]:>8,.0f}  median ${d[len(d)//2]:>8,.0f}  maximum ${d[-1]:>8,.0f}\n')
        fh.write('\nVALIDATION FLAGS (some records have multiple flags)\n')
        for k,v in issues.most_common():fh.write(f'{k}: {v}\n')
        fh.write('\nNOTES\n')
        fh.write('- MySQL Workbench export embedded unescaped JSON strings. Recovered and parsed all JSON records.\n')
        fh.write('- All source release_date fields were NULL; release_year came from JSON specifications.\n')
        fh.write('- 2017-to-2026 hardware included; 2017 GPUs typically use used-market rather than original MSRP assumptions.\n')
        fh.write('- Some source release years are inconsistent with model/socket; flagged for manual review.\n')
        fh.write('- Seed values are NOT source-verified individual quotes.\n')
    return output,issues

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=Path('null_prices_comopnents.csv'))
    parser.add_argument('--output',type=Path,default=Path('.'))
    args=parser.parse_args()
    res,issues=make_files(args.input,args.output)
    print(f'Processed {len(res)} rows. Saved preview CSV, flagged-rows CSV, guarded SQL and summary to {args.output}')
    print('Flag counts:',dict(issues))
