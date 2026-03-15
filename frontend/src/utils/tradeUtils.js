function formatCurrency(value) {
  if (value == null) return '';
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(value).trim();
}

function profitLossClass(value) {
  return value >= 0 ? "text-success" : "text-danger";
}

function formatValue(value) {
  return value?.toFixed(2) ?? '';
}

function formatDate(dateString) {
  if (!dateString) return '';
  // Append local time to prevent UTC interpretation shifting the date by one day
  const normalized = String(dateString).includes('T') ? dateString : `${dateString}T00:00:00`;
  return new Date(normalized).toLocaleDateString("en-US");
}

function rowClass(trade) {
  return {
    "table-warning": (trade.sells?.length || 0) > 0,
    "table-success": trade.current_sold_qty > 0,
  };
}

//TODO: Deal with Sell to open and Buy to close
function formatAction(trade) {
  return getFullAction(trade.action);
}

function getFullAction(code) {
  const actionMap = {
    BI: "Bank Interest",
    BOI: "Bond Interest",
    B: "Buy",
    BC: "Buy to Close",
    BO: "Buy to Open",
    CD: "Cash Dividend",
    CM: "Cash Merger",
    CMJ: "Cash Merger Adj",
    EE: "Exchange or Exercise",
    EXP: "Expired",
    FR: "Funds Received",
    IT: "Internal Transfer",
    J: "Journal",
    JS: "Journaled Shares",
    MT: "MoneyLink Transfer",
    PYDR: "Pr Yr Div Reinvest",
    QDR: "Qual Div Reinvest",
    QD: "Qualified Dividend",
    RS: "Reinvest Shares",
    RD: "Reinvest Dividend",
    RSP: "Reverse Split",
    S: "Sell",
    SC: "Sell to Close",
    SO: "Sell to Open",
    SSP: "Stock Split",
    TXW: "Tax Withholding",
  };

  return actionMap[code] || code;
}

function formatTradeType(trade) {
  return getFullTradeType(trade.trade_type);
}

function getFullTradeType(code) {
  const tradeType = {
    L: "Long",
    S: "Short",
    C: "Call",
    P: "Put",
    O: "Other",
  };

  return tradeType[code] || code;
}

export {
  formatAction,
  formatCurrency,
  formatTradeType,
  profitLossClass,
  formatValue,
  formatDate,
  rowClass,
};
