// Source: 2026-11-23 user correction (S05 in front of Zhili and Gauss has one even slope, no level stretch).
// Local model correction, not survey data. Applied as an additive offset to the shared road height field.
export const s05FrontageGrade={"road":218881800,"knotsZ":[-292,-170,-125.1],"smoothing":8,"rampNorth":21,"rampSouth":6,"core":21,"fade":30,"buildingBlend":2,"reference":"使用者記得S05在致理與高斯前坡度很平均、沒有完全平緩的段落。取致理北端(z=-292)、高斯南端(z=-170)、S27交口(z=-125.1，路口原高程不動)三個節點的原高程，相鄰兩節點各拉成單一均勻縱坡（約3%與約11%，後段原本就是約12%陡坡），節點處以±8m平均圓順，兩端用平滑漸變接回原高程；道路路線、路寬、建築與地形墊底不動。數值為模型近似，非實測。"};
