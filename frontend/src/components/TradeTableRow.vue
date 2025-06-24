<template>
    <td>{{ trade.trade_id + "-" + trade.account }}</td>
    <td>{{ formatTradeType(trade) }}</td>
    <!-- <td>{{ trade.action }}</td> -->
    <td>{{ formatAction(trade) }}</td>
    <td>{{ formatDate(trade.trade_date_iso) }}</td>

    <td v-if="trade.is_buy_trade">
        {{ trade.quantity }}
    </td>
    <td v-else>
    </td>

    <td>{{ trade.price }}</td>

    <!-- Basis Price -->
    <td :class="profitLossClass(trade.amount)">
        {{ trade.is_buy_trade ? formatCurrency(trade.amount || 0) : formatCurrency(trade.basis_amt || 0) }}
    </td>

    <td>{{ trade.is_buy_trade ? formatValue(trade.current_sold_qty) : trade.quantity }}</td>

    <!-- Sold Amonunt -->
    <td>{{ trade.is_buy_trade ? formatCurrency(trade.current_sold_amt) : formatCurrency(trade.amount) }}</td>

    <td :class="profitLossClass(trade.profit_loss)">
        {{ trade.is_buy_trade ? formatCurrency(trade.current_profit_loss) : formatCurrency(trade.profit_loss) }}
    </td>

    <td :class="profitLossClass(trade.percent_profit_loss)">
        <div v-if="trade.is_buy_trade">
            {{ formatValue(trade.current_percent_profit_loss) }} {{ trade.current_percent_profit_loss ? "%" : "" }}
        </div>
        <div v-else>
            {{ formatValue(trade.percent_profit_loss) }} {{ trade.percent_profit_loss ? "%" : "" }}
        </div>
    </td>

    <td>{{ trade.is_buy_trade ? trade.is_done === true ? "Closed" : "Open" : "" }}</td>
</template>

<script>
import { formatAction, formatCurrency, formatTradeType, profitLossClass, formatValue, formatDate, rowClass } from '@/utils/tradeUtils.js';

export default {
    components: {},
    props: {
        trade: {
            type: Object,
            required: true
        },
        stockType: {
            type: String,
            required: false
        },
    },
    methods: {
        formatAction,
        formatCurrency,
        formatTradeType,
        profitLossClass,
        formatValue,
        formatDate,
        rowClass,
    },
};
</script>