// S06 (詠霽路 293423729) east-side planter. User site observation 2026-11-22: from the Huanyu (寰宇) platform up to the
// S21 junction there is a ~100 cm wide (user first said 30 cm, corrected to 100 cm on 2026-11-22) grass bed beside the road, so the walkway sits 30 cm further from the road.
// Stations are metres along the prepared route (routeSections().distance); side -1 = east (same as the sidewalk).
// Width is the user's ~30 cm; the 6 m ease-in, the grass lip (rise) and the stop just inside the S21 mouth are model choices.
export const s06Planter={
 road:293423729,
 side:-1,
 from:182.5,   // end of the Huanyu T platform bar (154.5-182.5 m); the sidewalk meets it unshifted
 taper:10,     // smooth ease from 0 to the full setback so the walkway edge never jumps
 to:285,       // inside the S21 mouth (S21 meets S06 at 286.6 m; the asphalt there removes the sidewalk 282.9-287.2 m)
 width:1,
 rise:.11      // grass top above the road surface; the walkway is 0.15 above, so its curb face shows 4 cm
};
const smooth=t=>{t=Math.max(0,Math.min(1,t));return t*t*(3-2*t);};
// Setback of the sidewalk inner edge at both ends of a route segment. A segment that crosses `to` holds its start value so
// the cut falls on a single section, inside the junction asphalt.
export function setbackPair(osm,aDistance,bDistance,config=s06Planter){
 if(osm!==config.road)return[0,0];
 const at=d=>d>config.to?0:config.width*smooth((d-config.from)/config.taper),sa=at(aDistance);
 return[sa,aDistance<=config.to&&bDistance>config.to?sa:at(bDistance)];
}
