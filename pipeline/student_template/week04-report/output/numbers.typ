File #raw("inventory-week03.csv"): $n=10$ usable values of inventory item scores (column #raw("scored")). Mean = $3.00$, SD = $1.15$. 0 row(s) excluded; scores outside 1–5 were excluded.

#table(
  columns: (auto, auto),
  inset: 6pt,
  stroke: 0.4pt,
  [*Statistic*], [*Value*],
  [$n$], [10],
  [Mean], [3.00],
  [SD], [1.15],
  [Excluded], [0],
)

#figure(
  image("figure.png", width: 90%),
  caption: [Counts of usable inventory item scores after reverse scoring.],
)
