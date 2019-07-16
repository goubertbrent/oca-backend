export function getReach(userCount: number) {
  const lowerGuess = Math.round(userCount * 0.125);
  const higherGuess = Math.round(userCount * 0.25);
  return { lowerGuess, higherGuess };
}

export function getCost(currency: string, minUsers: number, maxUsers: number) {
  const factor = 50.00 / 10000;  // 10000 views for 50 euro
  const minCost = minUsers * factor;
  const maxCost = maxUsers * factor;
  return `${currency} ${minCost.toFixed(2)} - ${currency} ${maxCost.toFixed(2)}`;
}
