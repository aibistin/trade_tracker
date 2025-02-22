<template>
    <table class="table table-responsive table-bordered table-dark table-hover text-center">
        <thead>
            <tr>
                <th colspan="12">Trades for <span class="text-emphasis">{{ stockSymbol }}</span></th>
            </tr>
            <tr>
                <th>ID</th>
                <th>Type</th>
                <th>Acct</th>
                <th>Date</th>
                <th>Qty</th>
                <th>Cost Price</th>
                <th>Basis/Revenue</th>
                <th>Sold Qty</th>
                <th>Sold Amt.</th>
                <th>Profit/Loss</th>
                <th>Profit/Loss %</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            <slot></slot>
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
    },
    methods: {}
};
</script>