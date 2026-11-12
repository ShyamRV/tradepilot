export const money = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0
});

export const price = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR"
});

export const pct = (value: number, digits = 2) =>
  `${value >= 0 ? "+" : ""}${value.toFixed(digits)}%`;
