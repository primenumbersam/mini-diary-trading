/* ==========================================================================
   Global App Store (Theme, Sidebar, Navigation) & Advanced DataGrid Controllers
   ========================================================================== */

function setupDataGridCore(config) {
  return {
    rawItems: config.items || [],
    cols: config.cols || {},
    showColMenu: false,
    openMenuId: null,

    // Search & Filter
    searchQuery: '',
    filterCountry: 'all',
    filterClass: 'all',
    filterInstrument: 'all',
    filterSide: 'all',
    filterStatus: 'all',
    filterAction: 'all',
    filterAsset: 'all',

    // Grouping & Sorting
    groupBy: config.defaultGroupBy || 'none',
    sortCol: config.defaultSortCol || 'id',
    sortAsc: config.defaultSortAsc !== undefined ? config.defaultSortAsc : true,

    // Modal
    showEditModal: false,
    editItem: {},

    init() {
      const refreshIcons = () => {
        this.$nextTick(() => {
          if (window.lucide) window.lucide.createIcons();
        });
      };
      this.$watch('searchQuery', refreshIcons);
      this.$watch('filterCountry', refreshIcons);
      this.$watch('filterClass', refreshIcons);
      this.$watch('filterInstrument', refreshIcons);
      this.$watch('filterSide', refreshIcons);
      this.$watch('filterStatus', refreshIcons);
      this.$watch('filterAction', refreshIcons);
      this.$watch('filterAsset', refreshIcons);
      this.$watch('groupBy', refreshIcons);
      this.$watch('sortCol', refreshIcons);
      this.$watch('sortAsc', refreshIcons);
      this.$watch('showEditModal', refreshIcons);
      refreshIcons();
    },

    sortBy(col) {
      if (this.sortCol === col) {
        this.sortAsc = !this.sortAsc;
      } else {
        this.sortCol = col;
        this.sortAsc = true;
      }
    },

    get processedItems() {
      let items = [...this.rawItems];

      // Asset & Keyword Search (Prioritizing asset_id)
      if (this.searchQuery && String(this.searchQuery).trim() !== '') {
        const q = String(this.searchQuery).trim().toLowerCase();
        items = items.filter(item => {
          const assetId = String(item.asset_id || '').toLowerCase();
          const assetName = String(item.asset_name || '').toLowerCase();
          const memo = String(item.plan_memo || item.trade_memo || item.asset_description || '').toLowerCase();
          const id = String(item.plan_id || item.trade_id || '').toLowerCase();
          return assetId.includes(q) || assetName.includes(q) || id.includes(q) || memo.includes(q);
        });
      }

      // Filters
      if (this.filterCountry && this.filterCountry !== 'all') {
        items = items.filter(item => item.asset_country === this.filterCountry);
      }
      if (this.filterClass && this.filterClass !== 'all') {
        items = items.filter(item => item.asset_class === this.filterClass);
      }
      if (this.filterInstrument && this.filterInstrument !== 'all') {
        items = items.filter(item => item.instrument_type === this.filterInstrument);
      }
      if (this.filterSide && this.filterSide !== 'all') {
        items = items.filter(item => item.position_side === this.filterSide);
      }
      if (this.filterStatus && this.filterStatus !== 'all') {
        items = items.filter(item =>
          item.plan_status === this.filterStatus ||
          item.asset_status === this.filterStatus ||
          item.trade_status === this.filterStatus
        );
      }
      if (this.filterAction && this.filterAction !== 'all') {
        items = items.filter(item => item.trade_action === this.filterAction);
      }
      if (this.filterAsset && this.filterAsset !== 'all') {
        items = items.filter(item => item.asset_id === this.filterAsset);
      }

      // Dynamic Sorting
      if (this.sortCol) {
        items.sort((a, b) => {
          let vA = a[this.sortCol];
          let vB = b[this.sortCol];

          if (vA === null || vA === undefined) vA = '';
          if (vB === null || vB === undefined) vB = '';

          if (typeof vA === 'number' && typeof vB === 'number') {
            return this.sortAsc ? vA - vB : vB - vA;
          }

          const strA = String(vA).toLowerCase();
          const strB = String(vB).toLowerCase();
          if (strA < strB) return this.sortAsc ? -1 : 1;
          if (strA > strB) return this.sortAsc ? 1 : -1;
          return 0;
        });
      }

      return items;
    },

    get displayRows() {
      const items = this.processedItems;
      if (!this.groupBy || this.groupBy === 'none') {
        return items.map((item, idx) => ({
          _rowType: 'data',
          _rowKey: 'd-' + (item.plan_id || item.trade_id || (item.asset_id ? item.asset_id + '-' + idx : idx)),
          data: item
        }));
      }

      const groups = {};
      items.forEach((item, idx) => {
        const rawKey = item[this.groupBy];
        const key = (rawKey !== null && rawKey !== undefined && rawKey !== '') ? String(rawKey) : 'Unassigned';
        if (!groups[key]) groups[key] = [];
        groups[key].push({ item, idx });
      });

      const rows = [];
      Object.keys(groups).forEach(key => {
        const groupLabel = `${this.groupBy.replace('_', ' ').toUpperCase()}: ${key} (${groups[key].length})`;
        rows.push({
          _rowType: 'group',
          _rowKey: 'g-' + key,
          label: groupLabel
        });
        groups[key].forEach(({ item, idx }) => {
          rows.push({
            _rowType: 'data',
            _rowKey: 'd-' + key + '-' + (item.plan_id || item.trade_id || (item.asset_id ? item.asset_id + '-' + idx : idx)),
            data: item
          });
        });
      });

      return rows;
    },

    openEdit(item) {
      this.editItem = JSON.parse(JSON.stringify(item));
      this.showEditModal = true;
      this.openMenuId = null;
    },

    closeEdit() {
      this.showEditModal = false;
      this.editItem = {};
    }
  };
}

function assetsGrid(items) {
  const core = setupDataGridCore({
    items: items || [],
    cols: {
      symbol: true,
      name: true,
      price: true,
      country: true,
      class: true,
      status: true,
      actions: true
    },
    defaultSortCol: 'asset_id',
    defaultSortAsc: true
  });

  return {
    ...core,
    newSymbol: '',
    newName: '',
    newClass: 'cash',
    newCountry: '',
    newDesc: '',

    duplicateAsset(id, name, cls, country, desc) {
      this.newSymbol = id + '_COPY';
      this.newName = name;
      this.newClass = cls;
      this.newCountry = country;
      this.newDesc = desc;
      this.openMenuId = null;
    }
  };
}

function plansGrid(items) {
  const core = setupDataGridCore({
    items: items || [],
    cols: {
      date: true,
      asset: true,
      instrument: true,
      side: true,
      entry: true,
      tp: true,
      qty: true,
      value: true,
      rrr: true,
      confidence: true,
      status: true,
      actions: true
    },
    defaultSortCol: 'plan_date',
    defaultSortAsc: false
  });

  return {
    ...core,
    newEntry: '',
    newTp: '',
    newSl: '',
    newAssetId: '',
    newSide: 'long',
    newInstrumentType: 'spot',
    newPlanDate: new Date().toISOString().split('T')[0],
    newPlanQty: '',
    newPlanConfidence: 'medium',
    newPlanMemo: '',

    calcRrr() {
      const entry = parseFloat(this.newEntry);
      const tp = parseFloat(this.newTp);
      const sl = parseFloat(this.newSl);
      if (!entry || !tp || !sl || isNaN(entry) || isNaN(tp) || isNaN(sl)) return '0.00';
      const risk = Math.abs(entry - sl);
      if (risk === 0) return '0.00';
      const reward = Math.abs(tp - entry);
      return (reward / risk).toFixed(2);
    },

    duplicatePlan(asset, instrument, entry, tp, sl, qty, confidence) {
      this.newAssetId = asset;
      this.newInstrumentType = instrument || 'spot';
      this.newEntry = entry;
      this.newTp = tp;
      this.newSl = sl;
      this.newPlanQty = qty;
      this.newPlanConfidence = confidence || 'medium';
      this.openMenuId = null;
    }
  };
}

function tradesGrid(trades, assets, plans) {
  const core = setupDataGridCore({
    items: trades || [],
    cols: {
      date: true,
      asset: true,
      action: true,
      instrument: true,
      side: true,
      price: true,
      tp: true,
      qty: true,
      value: true,
      fee: true,
      status: true,
      actions: true
    },
    defaultSortCol: 'trade_datetime',
    defaultSortAsc: false
  });

  return {
    ...core,
    allPlans: plans || [],
    allAssets: assets || [],
    newDatetime: new Date(new Date().getTime() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 16),
    newAction: 'open',
    newAsset: '',
    newSide: 'long',
    newPrice: '',
    newQty: '',
    newFee: '',
    newTp: '',
    newSl: '',
    newPlanId: '',
    newMemo: '',

    get availablePlansForAsset() {
      if (!this.newAsset) return [];
      const ticker = this.newAsset.trim().toUpperCase();
      return this.allPlans.filter(p => p.asset_id && p.asset_id.toUpperCase() === ticker);
    },

    onAssetInput(val) {
      this.newAsset = val ? val.trim().toUpperCase() : '';
      if (this.newPlanId) {
        const matching = this.availablePlansForAsset.find(p => p.plan_id === this.newPlanId);
        if (!matching) this.newPlanId = '';
      }
    },

    onActionChange() {
      if (this.newAction === 'deposit' || this.newAction === 'withdraw') {
        this.newAsset = 'CASH_USD';
        this.newPrice = '1.0';
        this.newSide = 'neutral';
        this.newTp = '';
        this.newSl = '';
        this.newPlanId = '';
      } else if (this.newAsset === 'CASH_USD') {
        this.newAsset = '';
        this.newPrice = '';
        this.newSide = 'long';
      }
    },

    onPlanSelectChange(planId) {
      this.newPlanId = planId || '';
      if (!planId) return;
      const selected = this.allPlans.find(p => p.plan_id === planId);
      if (selected) {
        if (selected.position_side) this.newSide = selected.position_side;
        if (selected.plan_entry_price) this.newPrice = selected.plan_entry_price;
        if (selected.plan_qty) this.newQty = selected.plan_qty;
        if (selected.plan_tp_price) this.newTp = selected.plan_tp_price;
        if (selected.plan_sl_price) this.newSl = selected.plan_sl_price;
        if (selected.plan_memo) this.newMemo = selected.plan_memo;
      }
    },

    calcTradeValue() {
      const price = parseFloat(this.newPrice);
      const qty = parseFloat(this.newQty);
      if (isNaN(price) || isNaN(qty)) return '0.00';
      return (price * qty).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    },

    duplicateTrade(asset, action, side, price, qty, fee, tp, sl, planId) {
      this.newAsset = asset;
      this.newAction = action;
      this.newSide = side;
      this.newPrice = price;
      this.newQty = qty;
      this.newFee = fee;
      this.newTp = tp || '';
      this.newSl = sl || '';
      this.newPlanId = planId || '';
      this.newDatetime = new Date(new Date().getTime() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 16);
      this.openMenuId = null;
    }
  };
}

// Register global functions for direct window access & Alpine.data
window.assetsGrid = assetsGrid;
window.plansGrid = plansGrid;
window.tradesGrid = tradesGrid;

document.addEventListener('alpine:init', () => {
  const isMobile = window.innerWidth <= 768;
  const savedState = localStorage.getItem('sidebar_state');
  const initialSidebarOpen = isMobile ? false : (savedState !== 'closed');

  Alpine.store('app', {
    sidebarOpen: initialSidebarOpen,
    isDark: document.documentElement.classList.contains('dark'),
    userMenuOpen: false,

    toggleSidebar() {
      this.sidebarOpen = !this.sidebarOpen;
      if (window.innerWidth > 768) {
        localStorage.setItem('sidebar_state', this.sidebarOpen ? 'open' : 'closed');
      }
      setTimeout(() => { if (window.lucide) lucide.createIcons(); }, 50);
    },

    closeSidebarOnMobile() {
      if (window.innerWidth <= 768) {
        this.sidebarOpen = false;
      }
    },

    toggleTheme() {
      this.isDark = !this.isDark;
      if (this.isDark) {
        document.documentElement.classList.add('dark');
        localStorage.setItem('theme', 'dark');
      } else {
        document.documentElement.classList.remove('dark');
        localStorage.setItem('theme', 'light');
      }
      setTimeout(() => { if (window.lucide) lucide.createIcons(); }, 50);
    }
  });

  Alpine.data('assetsGrid', assetsGrid);
  Alpine.data('plansGrid', plansGrid);
  Alpine.data('tradesGrid', tradesGrid);
});
