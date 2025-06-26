/*
 This is a Vue.js component that provides utility functions for formatting trade data.
It will export formatCurrency, profitLossClass, formatValue, formatDate, rowClass
*/
function formatCurrency(value) {

  if (!value) {
    return null;
  }   

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    currencySign: "accounting",
  })
    .format(value)
    .trim();
}

function profitLossClass(value) {
  return value >= 0 ? "text-success" : "text-danger";
}

function formatValue(value) {
  // return value ? value.toFixed(2) : null
  return value.toFixed(2)
}

function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString("en-US");
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
  return getFullTradeType(trade.trade_type); // trade_type is a property of the trade object
}

function getFullTradeType(code) {
  const tradeType = {
    L: "Long",
    S: "Short",
    C: "Call",
    P: "Put ",
    O: "Other",
  };

  return tradeType[code] || code;
}

function logRoute(route) {
  console.log(
    "Route: ",
    Object.keys(route).forEach((key) =>
      console.log(`K: ${key} => V: ${route[key]}`)
    )
  );
  console.log(`Path: ${route.path}`); //all_trades/ALAB
  console.log(`Name: ${route.name}`); // AllTrades
  console.log(`Params: `, route.params); // {stockSymbol: "ALAB"}
  console.log(`Query: `, route.query);
  console.log(`Hash: ${route.hash}`); // empty
  console.log(`Full Path: ${route.fullPath}`); // /all_trades/ALAB:w
  console.log(`Matched: `, route.matched); // Array of matched routes
  console.log(`Meta: `, route.meta);
  console.log(`Redirected From: ${route.redirectedFrom}`); // empty
  console.log(`Route Symbol: ${route.params.stockSymbol}`); //good
}

export {
  formatAction,
  formatCurrency,
  formatTradeType,
  profitLossClass,
  formatValue,
  formatDate,
  logRoute,
  rowClass,
};
