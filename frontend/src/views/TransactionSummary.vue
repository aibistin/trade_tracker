<template>

  <table class="table table-primary table-hover table-bordered border-primary table-striped-columns text-center">
    <thead>
      <tr>
        <th colspan="13"><span class="text-primary-emphasis">{{ stockSymbol }}</span> Transaction Summary</th>
      </tr>
      <tr >
        <!-- <th colspan="1"></th> -->
        <th colspan="3">Bought</th>
        <th colspan="4">Sold</th>
        <th colspan="3">Unsold</th>
        <th colspan="3">Result</th>
      </tr>
      <tr >
        <!-- <th>Symbol</th> -->
        <th>Total Qty</th>
        <th>Avg Price</th>
        <th>Cost Basis</th>

        <th>Qty</th>
        <th>Avg Cost Price</th>
        <th>Cost Basis</th>
        <th>Revenue</th>

        <th>Qty</th>
        <th>Avg Cost Price</th>
        <th>Cost Basis</th>
        <th>Profit/Loss</th>
        <th>Profit/Loss %</th>
        <th>Trade Ct</th>
      </tr>
    </thead>
    <tbody>
      <tr class="table-secondary align-middle">
        <!-- <td>{{ tradeSummary.symbol }}</td> -->
        <td>{{ tradeSummary.bought_quantity }}</td>
        <td>{{ formatCurrency(Math.abs(tradeSummary.average_bought_price || 0)) }}</td>

        <td :class="profitLossClass(tradeSummary.bought_amount)">
          {{ formatCurrency(tradeSummary.bought_amount || 0) }}
        </td>

        <!-- <td>{{ tradeSummary.closed_bought_quantity }}</td> -->
        <td>{{ tradeSummary.sold_quantity }}</td>

        <td>{{ formatCurrency(tradeSummary.average_basis_sold_price || 0) }}</td>

        <td :class="profitLossClass(tradeSummary.closed_bought_amount)">
          {{ formatCurrency(tradeSummary.closed_bought_amount || 0) }}
        </td>

        <td>{{ formatCurrency(tradeSummary.sold_amount || 0) }}</td>
        <!-- <td>{{ formatCurrency(tradeSummary.average_sold_price) }}</td> -->

        <td>{{ tradeSummary.open_bought_quantity }}</td>
        <td>{{ formatCurrency(tradeSummary.average_basis_open_price || 0) }}</td>

        <td>{{ formatCurrency(tradeSummary.open_bought_amount || 0) }}</td>

        <!-- <td>{{ tradeSummary.sold_quantity }}</td> -->
        <td :class="profitLossClass(tradeSummary.profit_loss)">
          {{ formatCurrency(tradeSummary.profit_loss) }}
        </td>
        <td :class="profitLossClass(tradeSummary.percent_profit_loss)">
          {{ formatValue(tradeSummary.percent_profit_loss) }}%
        </td>
        <td>{{ allTradeCount }}</td>
      </tr>
    </tbody>
  </table>
</template>

<script>
export default {
  props: {
    stockSymbol: {
      type: String,
      required: true
    },
    tradeSummary: {
      type: Object,
      required: true
    },
    allTradeCount: {
      type: Number,
      default: 0
    },
  },
  methods: {
    formatCurrency(value) {
      return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', currencySign: 'accounting' }).format(value).trim();
    },
    profitLossClass(value) {
      return value >= 0 ? 'text-success' : 'text-danger';
    },
    formatValue(value) {
      return value.toFixed(2);
    }
  }
};
</script>