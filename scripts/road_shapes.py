"""Share tapered runtime road envelopes with offline junction and map builders."""
import json,subprocess
from pathlib import Path
from shapely.geometry import Polygon
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[1]
def motor_shape(fillets=False):
 js="""import fs from'node:fs';import{createRoadNetwork}from'./roads.js';import{pavementIndex}from'./pavement.js';const c=JSON.parse(fs.readFileSync('data/campus.json')),n=createRoadNetwork(c.roads,()=>0,{}, {apron:c.entranceApron,pavedAreas:c.pavedAreas,junctionFillets:FILLETS?c.junctionFillets:[]});process.stdout.write(JSON.stringify(pavementIndex(n).all.filter(p=>!p.actual).map(p=>p.points)));""".replace('FILLETS','true' if fillets else 'false')
 return unary_union([Polygon(p).buffer(0) for p in json.loads(subprocess.check_output(['node','--input-type=module','-e',js],cwd=ROOT))])
