/**
 * Format a number as currency (USD).
 * @param {number} amount - The amount to format.
 * @param {boolean} showDollarSign - Whether to include the dollar sign.
 * @returns {string} The formatted currency string.
 */
export const formatCurrency = (amount, showDollarSign = true) => {
  const formatter = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  });
  
  const formatted = formatter.format(amount);
  return showDollarSign ? formatted : formatted.replace('$', '');
};

/**
 * Format a number with commas for thousands.
 * @param {number} number - The number to format.
 * @returns {string} The formatted number string.
 */
export const formatNumber = (number) => {
  return new Intl.NumberFormat('en-US').format(number);
};

/**
 * Format a percentage value.
 * @param {number} value - The decimal value to format (e.g., 0.05 for 5%).
 * @param {boolean} showSymbol - Whether to include the percent symbol.
 * @returns {string} The formatted percentage string.
 */
export const formatPercentage = (value, showSymbol = true) => {
  const percentage = (value * 100).toFixed(1);
  return showSymbol ? `${percentage}%` : percentage;
}; 