<template>
    <td>{{ buyTrade.trade_id }}</td>
    <td>{{ buyTrade.isBuy ? "Buy" : "Sell" }}</td>
    <td>{{ buyTrade.account }}</td>
    <td>{{ formatDate(buyTrade.trade_date_iso) }}</td>

    <td v-if="buyTrade.isBuy">
        {{ buyTrade.bought_quantity }}
    </td>
    <td v-else>
    </td>


    <td>{{ buyTrade.price }}</td>

    <td :class="profitLossClass(buyTrade.bought_amount)">
        {{ formatCurrency(buyTrade.bought_amount || 0) }}
    </td>

    <td>{{ buyTrade.sold_quantity }}</td>

    <td>{{ formatCurrency(buyTrade.sold_amount || 0) }}</td>

    <td :class="profitLossClass(buyTrade.profit_loss)">
        {{ formatCurrency(buyTrade.profit_loss) }}
    </td>

    <td :class="profitLossClass(buyTrade.percent_profit_loss)">
        {{ formatValue(buyTrade.percent_profit_loss) }}%
    </td>
    <td>{{ buyTrade.isClosed }}</td>
</template>

<script>
import { formatCurrency, profitLossClass, formatValue, formatDate, rowClass } from '@/utils/tradeUtils.js';

export default {
    components: {},
    props: {
        buyTrade: {
            type: Object,
            required: true
        },
    },
    methods: {
        formatCurrency,
        profitLossClass,
        formatValue,
        formatDate,
        rowClass,
    },
};
</script>