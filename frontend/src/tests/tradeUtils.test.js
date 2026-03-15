import { describe, it, expect } from 'vitest';
import {
  formatCurrency,
  profitLossClass,
  formatValue,
  formatDate,
  formatTradeType,
  formatAction,
  rowClass,
} from '@/utils/tradeUtils.js';

describe('formatCurrency', () => {
  it('formats a positive number as USD', () => {
    expect(formatCurrency(1234.56)).toBe('$1,234.56');
  });

  it('formats a negative number with a minus sign', () => {
    expect(formatCurrency(-42.5)).toBe('-$42.50');
  });

  it('formats zero', () => {
    expect(formatCurrency(0)).toBe('$0.00');
  });

  it('returns empty string for null', () => {
    expect(formatCurrency(null)).toBe('');
  });

  it('returns empty string for undefined', () => {
    expect(formatCurrency(undefined)).toBe('');
  });

  it('handles integer values', () => {
    expect(formatCurrency(100)).toBe('$100.00');
  });
});

describe('profitLossClass', () => {
  it('returns text-success for positive values', () => {
    expect(profitLossClass(100)).toBe('text-success');
  });

  it('returns text-success for zero', () => {
    expect(profitLossClass(0)).toBe('text-success');
  });

  it('returns text-danger for negative values', () => {
    expect(profitLossClass(-1)).toBe('text-danger');
  });
});

describe('formatValue', () => {
  it('formats a float to 2 decimal places', () => {
    expect(formatValue(3.14159)).toBe('3.14');
  });

  it('returns empty string for null', () => {
    expect(formatValue(null)).toBe('');
  });

  it('returns empty string for undefined', () => {
    expect(formatValue(undefined)).toBe('');
  });

  it('formats zero', () => {
    expect(formatValue(0)).toBe('0.00');
  });
});

describe('formatDate', () => {
  it('returns empty string for null', () => {
    expect(formatDate(null)).toBe('');
  });

  it('returns empty string for empty string', () => {
    expect(formatDate('')).toBe('');
  });

  it('formats a date string without shifting due to UTC interpretation', () => {
    // "2024-06-15" must render as 6/15/2024, not 6/14/2024
    const result = formatDate('2024-06-15');
    expect(result).toBe('6/15/2024');
  });

  it('formats a datetime string correctly', () => {
    const result = formatDate('2024-01-01T12:00:00');
    expect(result).toBe('1/1/2024');
  });
});

describe('formatTradeType', () => {
  it.each([
    [{ trade_type: 'L' }, 'Long'],
    [{ trade_type: 'S' }, 'Short'],
    [{ trade_type: 'C' }, 'Call'],
    [{ trade_type: 'P' }, 'Put'],
    [{ trade_type: 'O' }, 'Other'],
  ])('formats trade_type %s correctly', (trade, expected) => {
    expect(formatTradeType(trade)).toBe(expected);
  });

  it('returns the raw code for unknown trade types', () => {
    expect(formatTradeType({ trade_type: 'X' })).toBe('X');
  });

  it('Put has no trailing space', () => {
    expect(formatTradeType({ trade_type: 'P' })).toBe('Put');
  });
});

describe('formatAction', () => {
  it('formats known action codes', () => {
    expect(formatAction({ action: 'B' })).toBe('Buy');
    expect(formatAction({ action: 'S' })).toBe('Sell');
    expect(formatAction({ action: 'BO' })).toBe('Buy to Open');
    expect(formatAction({ action: 'SC' })).toBe('Sell to Close');
    expect(formatAction({ action: 'EXP' })).toBe('Expired');
  });

  it('returns the raw code for unknown action codes', () => {
    expect(formatAction({ action: 'UNKNOWN' })).toBe('UNKNOWN');
  });
});

describe('rowClass', () => {
  it('returns table-warning when trade has sells', () => {
    const classes = rowClass({ sells: [{}], current_sold_qty: 0 });
    expect(classes['table-warning']).toBe(true);
    expect(classes['table-success']).toBe(false);
  });

  it('returns table-success when current_sold_qty > 0', () => {
    const classes = rowClass({ sells: [], current_sold_qty: 5 });
    expect(classes['table-success']).toBe(true);
  });

  it('handles missing sells gracefully', () => {
    const classes = rowClass({ current_sold_qty: 0 });
    expect(classes['table-warning']).toBe(false);
  });
});
