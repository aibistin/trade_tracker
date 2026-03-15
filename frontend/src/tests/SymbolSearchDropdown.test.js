import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import SymbolSearchDropdown from '@/components/SymbolSearchDropdown.vue';

const symbols = [
  ['AAPL', 'Apple Inc.'],
  ['MSFT', 'Microsoft Corporation'],
  ['TSLA', 'Tesla Inc.'],
];

describe('SymbolSearchDropdown', () => {
  it('renders the search input', () => {
    const wrapper = mount(SymbolSearchDropdown, { props: { symbols } });
    expect(wrapper.find('input').exists()).toBe(true);
  });

  it('does not show dropdown before focus', () => {
    const wrapper = mount(SymbolSearchDropdown, { props: { symbols } });
    expect(wrapper.find('.dropdown-menu').exists()).toBe(false);
  });

  it('shows dropdown with all symbols on focus', async () => {
    const wrapper = mount(SymbolSearchDropdown, { props: { symbols } });
    await wrapper.find('input').trigger('focus');
    const items = wrapper.findAll('.dropdown-item');
    expect(items).toHaveLength(3);
  });

  it('filters symbols as user types', async () => {
    const wrapper = mount(SymbolSearchDropdown, { props: { symbols } });
    await wrapper.find('input').trigger('focus');
    await wrapper.find('input').setValue('apple');
    const items = wrapper.findAll('.dropdown-item:not(.disabled)');
    expect(items).toHaveLength(1);
    expect(items[0].text()).toContain('AAPL');
  });

  it('filters by symbol ticker', async () => {
    const wrapper = mount(SymbolSearchDropdown, { props: { symbols } });
    await wrapper.find('input').trigger('focus');
    await wrapper.find('input').setValue('MSF');
    const items = wrapper.findAll('.dropdown-item:not(.disabled)');
    expect(items).toHaveLength(1);
    expect(items[0].text()).toContain('MSFT');
  });

  it('shows "No matching symbols" when filter has no results', async () => {
    const wrapper = mount(SymbolSearchDropdown, { props: { symbols } });
    await wrapper.find('input').trigger('focus');
    await wrapper.find('input').setValue('ZZZZ');
    expect(wrapper.text()).toContain('No matching symbols found');
  });

  it('emits select event with the symbol on item click', async () => {
    const wrapper = mount(SymbolSearchDropdown, { props: { symbols } });
    await wrapper.find('input').trigger('focus');
    await wrapper.findAll('.dropdown-item')[0].trigger('mousedown');
    expect(wrapper.emitted('select')).toBeTruthy();
    expect(wrapper.emitted('select')[0]).toEqual(['AAPL']);
  });

  it('clears the search query after selection', async () => {
    const wrapper = mount(SymbolSearchDropdown, { props: { symbols } });
    const input = wrapper.find('input');
    await input.trigger('focus');
    await input.setValue('apple');
    await wrapper.findAll('.dropdown-item')[0].trigger('mousedown');
    expect(input.element.value).toBe('');
  });

  it('handles empty symbols array without throwing', async () => {
    const wrapper = mount(SymbolSearchDropdown, { props: { symbols: [] } });
    await wrapper.find('input').trigger('focus');
    expect(wrapper.find('.dropdown-menu').exists()).toBe(false);
  });

  it('is case-insensitive in search', async () => {
    const wrapper = mount(SymbolSearchDropdown, { props: { symbols } });
    await wrapper.find('input').trigger('focus');
    await wrapper.find('input').setValue('APPLE');
    const items = wrapper.findAll('.dropdown-item:not(.disabled)');
    expect(items).toHaveLength(1);
  });

  it('uses the placeholder prop', () => {
    const wrapper = mount(SymbolSearchDropdown, {
      props: { symbols, placeholder: 'Find a ticker…' },
    });
    expect(wrapper.find('input').attributes('placeholder')).toBe('Find a ticker…');
  });
});
