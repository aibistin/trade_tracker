/*
 This is a Vue.js component that provides utility functions for formatting trade data.
It will export formatCurrency, profitLossClass, formatValue, formatDate, rowClass
*/
function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', currencySign: 'accounting' }).format(value).trim();
}

function profitLossClass(value) {
    return value >= 0 ? 'text-success' : 'text-danger';
}

function formatValue(value) {
    return value.toFixed(2);
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US');
}

function rowClass(trade) {
    return {
        'table-warning': (trade.sells?.length || 0) > 0,
        'table-success': trade.current_sold_qty > 0
    };
}

function logRoute(route) {

  console.log("Route: ", Object.keys(route).forEach(key => console.log(`K: ${key} => V: ${route[key]}`)));
  console.log(`Path: ${route.path}`); //all_trades/ALAB
  console.log(`Name: ${route.name}`); // AllTrades
  console.log(`Params: `, route.params); // {stockSymbol: "ALAB"}
  console.log(`Query: `, route.query);
  console.log(`Hash: ${route.hash}`); // empty
  console.log(`Full Path: ${route.fullPath}`); // /all_trades/ALAB:w
  console.log(`Matched: `, route.matched); // Array of matched routes
  console.log(`Meta: `, route.meta);
  console.log(`Redirected From: ${route.redirectedFrom}`);   // empty
  console.log(`Route Symbol: ${route.params.stockSymbol}`); //good
};

export {
    formatCurrency,
    profitLossClass,
    formatValue,
    formatDate,
    logRoute,
    rowClass
};