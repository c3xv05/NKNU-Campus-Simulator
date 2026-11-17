# 生科地圖輪廓來源

`layout.json` 的 imageRing 是2026-11-17使用者提供之Google Maps截圖像素輪廓；localRing 是依該形狀整理、以S05正交軸表示的模型座標，公尺尺寸近似。imageRing不作貼圖或精確測量。

joint保留PR75已對齊致理／高斯的中央接點，localJoint是正交座標中的同一點。axis沿S05，另一軸為其東向法線。北棟A向南凸出細翼、南棟B向北凸出細翼，中間7.5m等寬通廊平行S05。

修改後執行：

```sh
python scripts/build-biology-layout.py
python scripts/build-building-catalog.py
```

再依 [通廊README](../campus-corridors/README.md) 由building-access開始重建。每棟原platformAnchor保留樓層高度，beforeOrthogonalSketch及beforeSouthAlignment只留歷史，不作現況恢復。
