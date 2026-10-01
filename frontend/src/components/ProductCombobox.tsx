import React, { useState, useRef, useEffect } from 'react';
import { Product } from '../api';

interface ProductComboboxProps {
  products: Product[];
  selectedProductId: string;
  onSelect: (productId: string) => void;
  disabled?: boolean;
}

export const getProductCategory = (name: string): { category: string; label: string; icon: string } => {
  const n = (name || '').toLowerCase();
  if (
    n.includes('atta') ||
    n.includes('rice') ||
    n.includes('dal') ||
    n.includes('flour') ||
    n.includes('sooji') ||
    n.includes('besan') ||
    n.includes('wheat') ||
    n.includes('sugar') ||
    n.includes('salt') ||
    n.includes('poha') ||
    n.includes('grain')
  ) {
    return { category: 'grains', label: 'Grains & Pulses', icon: '🌾' };
  }
  if (
    n.includes('tea') ||
    n.includes('coffee') ||
    n.includes('spice') ||
    n.includes('masala') ||
    n.includes('chilli') ||
    n.includes('turmeric') ||
    n.includes('haldi') ||
    n.includes('coriander') ||
    n.includes('jeera') ||
    n.includes('pepper')
  ) {
    return { category: 'pantry', label: 'Tea & Spices', icon: '🫖' };
  }
  if (
    n.includes('milk') ||
    n.includes('dairy') ||
    n.includes('curd') ||
    n.includes('dahi') ||
    n.includes('paneer') ||
    n.includes('butter') ||
    n.includes('cheese') ||
    n.includes('egg')
  ) {
    return { category: 'dairy', label: 'Dairy & Eggs', icon: '🥛' };
  }
  if (n.includes('oil') || n.includes('ghee')) {
    return { category: 'oils', label: 'Oils & Ghee', icon: '🥫' };
  }
  if (
    n.includes('soap') ||
    n.includes('detergent') ||
    n.includes('toothpaste') ||
    n.includes('cleaner') ||
    n.includes('harpic') ||
    n.includes('lizol') ||
    n.includes('vim') ||
    n.includes('rin') ||
    n.includes('surf') ||
    n.includes('tide') ||
    n.includes('colgate') ||
    n.includes('dettol') ||
    n.includes('lifebuoy')
  ) {
    return { category: 'hygiene', label: 'Household & Care', icon: '🧼' };
  }
  if (
    n.includes('biscuit') ||
    n.includes('cookie') ||
    n.includes('maggi') ||
    n.includes('noodles') ||
    n.includes('bhujia') ||
    n.includes('namkeen') ||
    n.includes('chips') ||
    n.includes('snack') ||
    n.includes('kurkure') ||
    n.includes('lays') ||
    n.includes('oreo') ||
    n.includes('parle') ||
    n.includes('britannia') ||
    n.includes('dark fantasy') ||
    n.includes('yippee')
  ) {
    return { category: 'snacks', label: 'Biscuits & Snacks', icon: '🍪' };
  }
  return { category: 'other', label: 'General Grocery', icon: '📦' };
};

export const ProductCombobox: React.FC<ProductComboboxProps> = ({
  products,
  selectedProductId,
  onSelect,
  disabled = false,
}) => {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [search, setSearch] = useState<string>('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const containerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  const selectedProduct = products.find((p) => p.id === selectedProductId);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  // Focus search input on open
  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isOpen]);

  const categories = [
    { id: 'all', label: 'All Items' },
    { id: 'grains', label: '🌾 Grains' },
    { id: 'oils', label: '🥫 Oils' },
    { id: 'pantry', label: '🫖 Spices' },
    { id: 'dairy', label: '🥛 Dairy' },
    { id: 'snacks', label: '🍪 Snacks' },
    { id: 'hygiene', label: '🧼 Care' },
  ];

  const filteredProducts = products.filter((p) => {
    const s = search.toLowerCase().trim();
    const matchesSearch =
      !s ||
      p.name.toLowerCase().includes(s) ||
      p.sku.toLowerCase().includes(s);

    const cat = getProductCategory(p.name).category;
    const matchesCategory = categoryFilter === 'all' || cat === categoryFilter;

    return matchesSearch && matchesCategory;
  });

  return (
    <div ref={containerRef} style={{ position: 'relative', width: '100%' }}>
      {/* ── ComboBox Trigger Box ── */}
      <div
        role="button"
        tabIndex={0}
        onClick={() => !disabled && setIsOpen((prev) => !prev)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            !disabled && setIsOpen((prev) => !prev);
          }
        }}
        style={{
          width: '100%',
          minHeight: '52px',
          background: disabled ? '#f8fafc' : '#ffffff',
          border: isOpen ? '2px solid #e23744' : '1.5px solid #cbd5e1',
          borderRadius: '12px',
          padding: '8px 14px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          cursor: disabled ? 'not-allowed' : 'pointer',
          boxShadow: isOpen
            ? '0 0 0 3px rgba(226, 55, 68, 0.15)'
            : '0 1px 3px rgba(0, 0, 0, 0.04)',
          transition: 'all 0.18s ease',
          userSelect: 'none',
        }}
      >
        {selectedProduct ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1, overflow: 'hidden' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '8px',
                background: '#fff1f2',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.25rem',
                flexShrink: 0,
              }}
            >
              {getProductCategory(selectedProduct.name).icon}
            </div>
            <div style={{ minWidth: 0, flex: 1 }}>
              <div
                style={{
                  fontWeight: 700,
                  fontSize: '0.94rem',
                  color: '#0f172a',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
              >
                {selectedProduct.name}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '2px' }}>
                <span
                  style={{
                    fontFamily: "'JetBrains Mono', monospace",
                    fontSize: '0.72rem',
                    color: '#64748b',
                    background: '#f1f5f9',
                    padding: '1px 6px',
                    borderRadius: '4px',
                  }}
                >
                  {selectedProduct.sku}
                </span>
                <span
                  style={{
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    color:
                      selectedProduct.current_stock < selectedProduct.reorder_level
                        ? '#dc2626'
                        : '#16a34a',
                  }}
                >
                  {selectedProduct.current_stock} in stock
                </span>
              </div>
            </div>
            <div style={{ textAlign: 'right', flexShrink: 0, marginRight: '10px' }}>
              <span
                style={{
                  fontSize: '1.05rem',
                  fontWeight: 800,
                  color: '#0f172a',
                }}
              >
                ₹{selectedProduct.selling_price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </span>
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#94a3b8' }}>
            <span style={{ fontSize: '1.1rem' }}>🔍</span>
            <span style={{ fontSize: '0.92rem', fontWeight: 500 }}>
              Search & select from {products.length} catalog items...
            </span>
          </div>
        )}

        <div
          style={{
            transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
            transition: 'transform 0.2s ease',
            color: '#64748b',
            fontSize: '0.75rem',
            marginLeft: '8px',
          }}
        >
          ▼
        </div>
      </div>

      {/* ── Floating Popover Menu ── */}
      {isOpen && (
        <div
          style={{
            position: 'absolute',
            top: 'calc(100% + 8px)',
            left: 0,
            right: 0,
            background: '#ffffff',
            borderRadius: '16px',
            border: '1.5px solid #cbd5e1',
            boxShadow:
              '0 20px 40px -8px rgba(15, 23, 42, 0.2), 0 0 0 1px rgba(226, 232, 240, 0.8)',
            zIndex: 1000,
            overflow: 'hidden',
            animation: 'fadeIn 0.15s ease-out',
          }}
        >
          {/* Top Search Input Box */}
          <div
            style={{
              padding: '12px 14px',
              borderBottom: '1px solid #f1f5f9',
              background: '#f8fafc',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                background: '#ffffff',
                border: '1.5px solid #e2e8f0',
                borderRadius: '10px',
                padding: '6px 12px',
                gap: '8px',
              }}
            >
              <span style={{ color: '#94a3b8', fontSize: '0.95rem' }}>🔍</span>
              <input
                ref={searchInputRef}
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search products by name, SKU, or category..."
                style={{
                  border: 'none',
                  outline: 'none',
                  width: '100%',
                  fontSize: '0.88rem',
                  fontFamily: 'inherit',
                  color: '#0f172a',
                }}
              />
              {search && (
                <button
                  type="button"
                  onClick={() => setSearch('')}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#94a3b8',
                    cursor: 'pointer',
                    fontSize: '0.85rem',
                    padding: '2px',
                  }}
                >
                  ✕
                </button>
              )}
            </div>

            {/* Category Filter Pills */}
            <div
              style={{
                display: 'flex',
                gap: '6px',
                marginTop: '10px',
                overflowX: 'auto',
                paddingBottom: '2px',
                scrollbarWidth: 'none',
              }}
            >
              {categories.map((cat) => (
                <button
                  key={cat.id}
                  type="button"
                  onClick={() => setCategoryFilter(cat.id)}
                  style={{
                    padding: '4px 10px',
                    borderRadius: '20px',
                    border: '1px solid',
                    borderColor: categoryFilter === cat.id ? '#e23744' : '#e2e8f0',
                    background: categoryFilter === cat.id ? '#e23744' : '#ffffff',
                    color: categoryFilter === cat.id ? '#ffffff' : '#64748b',
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    whiteSpace: 'nowrap',
                    transition: 'all 0.15s ease',
                  }}
                >
                  {cat.label}
                </button>
              ))}
            </div>
          </div>

          {/* Product Items List */}
          <div
            style={{
              maxHeight: '320px',
              overflowY: 'auto',
              padding: '6px',
            }}
          >
            <div
              style={{
                padding: '6px 12px',
                fontSize: '0.72rem',
                fontWeight: 700,
                color: '#94a3b8',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
              }}
            >
              Showing {filteredProducts.length} of {products.length} Products
            </div>

            {filteredProducts.length === 0 ? (
              <div
                style={{
                  padding: '32px 16px',
                  textAlign: 'center',
                  color: '#64748b',
                  fontSize: '0.88rem',
                }}
              >
                <div style={{ fontSize: '1.6rem', marginBottom: '6px' }}>📦</div>
                <div>No products found matching "{search}"</div>
                <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '4px' }}>
                  Try a different search term or category
                </div>
              </div>
            ) : (
              filteredProducts.map((p) => {
                const isSelected = p.id === selectedProductId;
                const catInfo = getProductCategory(p.name);
                const isLowStock = p.current_stock < p.reorder_level;

                return (
                  <div
                    key={p.id}
                    onClick={() => {
                      onSelect(p.id);
                      setIsOpen(false);
                      setSearch('');
                    }}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '10px 12px',
                      borderRadius: '10px',
                      background: isSelected ? '#fff1f2' : 'transparent',
                      border: isSelected ? '1px solid #fecdd3' : '1px solid transparent',
                      cursor: 'pointer',
                      transition: 'background 0.12s ease',
                      marginBottom: '2px',
                    }}
                    onMouseEnter={(e) => {
                      if (!isSelected) e.currentTarget.style.background = '#f8fafc';
                    }}
                    onMouseLeave={(e) => {
                      if (!isSelected) e.currentTarget.style.background = 'transparent';
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flex: 1, minWidth: 0 }}>
                      <div
                        style={{
                          width: '34px',
                          height: '34px',
                          borderRadius: '8px',
                          background: isSelected ? '#ffe4e6' : '#f1f5f9',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: '1.15rem',
                          flexShrink: 0,
                        }}
                      >
                        {catInfo.icon}
                      </div>

                      <div style={{ minWidth: 0, flex: 1 }}>
                        <div
                          style={{
                            fontWeight: isSelected ? 700 : 600,
                            fontSize: '0.9rem',
                            color: isSelected ? '#b91c1c' : '#0f172a',
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                          }}
                        >
                          {p.name}
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '2px' }}>
                          <span
                            style={{
                              fontFamily: "'JetBrains Mono', monospace",
                              fontSize: '0.7rem',
                              color: '#64748b',
                              background: '#f1f5f9',
                              padding: '1px 5px',
                              borderRadius: '4px',
                            }}
                          >
                            {p.sku}
                          </span>
                          <span
                            style={{
                              fontSize: '0.72rem',
                              fontWeight: 600,
                              color: isLowStock ? '#dc2626' : '#16a34a',
                            }}
                          >
                            {isLowStock ? '⚠️' : '✓'} {p.current_stock} in stock
                          </span>
                        </div>
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexShrink: 0 }}>
                      <div style={{ textAlign: 'right' }}>
                        <div
                          style={{
                            fontWeight: 800,
                            fontSize: '0.96rem',
                            color: '#0f172a',
                          }}
                        >
                          ₹{p.selling_price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </div>
                      </div>
                      {isSelected && (
                        <div
                          style={{
                            width: '20px',
                            height: '20px',
                            borderRadius: '50%',
                            background: '#e23744',
                            color: '#ffffff',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '0.7rem',
                            fontWeight: 700,
                          }}
                        >
                          ✓
                        </div>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
};
