<template>
    <table class="table table-responsive table-bordered table-dark table-hover text-center">
        <thead>
            <tr>
                <th colspan="12">{{ stockType }} Trades - <span class="text-emphasis">{{ stockSymbol }}</span></th>
            </tr>
            <tr>
                <th>ID-Acct</th>
                <th>Type</th>
                <th>Action</th>
                <th>Date</th>
                <th>{{ stockType === 'Option' ? 'Qty x 100' : 'Qty' }}</th>
                <th>Price</th>
                <th>Basis</th>
                <th>Sold Qty</th>
                <th>Sold Amt</th>
                <th>P/L</th>
                <th>P/L%</th>
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
        stockType: {
            type: String,
            required: true,
            default: "Stock"
        },
    },
    methods: {}
};
</script>