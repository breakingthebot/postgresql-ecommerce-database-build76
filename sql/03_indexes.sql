-- ============================================================================
-- PostgreSQL E-Commerce Database: Advanced Indexing Suite
-- Version: 1.2.0
-- Strategy: Composite B-Tree, Partial Indexes, Functional Expression Indexes,
--           and GIN (Generalized Inverted Index) for JSONB & Arrays.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. Composite B-Tree Indexes for High-Frequency Access Patterns
-- ----------------------------------------------------------------------------

-- Catalog faceted browsing: filter by category, active status, ordered by base_price
CREATE INDEX IF NOT EXISTS idx_products_category_status_price
    ON products (category_id, status, base_price);

-- Customer order history: rapid customer lookup sorted newest first
CREATE INDEX IF NOT EXISTS idx_orders_customer_placed_at
    ON orders (customer_id, placed_at DESC);

-- Order items joined by order and variant
CREATE INDEX IF NOT EXISTS idx_order_items_order_variant
    ON order_items (order_id, variant_id);

-- Product reviews sorted by rating and helpfulness
CREATE INDEX IF NOT EXISTS idx_reviews_product_rating_helpful
    ON reviews (product_id, rating DESC, helpful_votes DESC);

-- Category hierarchy traversal
CREATE INDEX IF NOT EXISTS idx_categories_parent_path
    ON categories (parent_id, hierarchy_path);

-- ----------------------------------------------------------------------------
-- 2. Partial Indexes for Hot Working Sets & Filtered Subsets
-- ----------------------------------------------------------------------------

-- Active & featured products for storefront homepages (avoids scanning archived/draft items)
CREATE INDEX IF NOT EXISTS idx_products_active_featured
    ON products (id, base_price)
    WHERE status = 'active' AND is_featured = true;

-- Fulfillment queue: only orders requiring warehouse processing (pending, paid, processing)
-- Over 90% of completed historical orders are excluded, keeping index tiny and buffer-hot
CREATE INDEX IF NOT EXISTS idx_orders_unfulfilled_queue
    ON orders (placed_at, order_number)
    WHERE status IN ('pending', 'paid', 'processing');

-- Inventory reorder alerts: only variants where stock is below threshold
CREATE INDEX IF NOT EXISTS idx_inventory_reorder_alerts
    ON inventory (variant_id, warehouse_code)
    WHERE quantity_on_hand <= reorder_point;

-- Active coupons currently eligible for redemption
CREATE INDEX IF NOT EXISTS idx_coupons_active_valid
    ON coupons (code, discount_type, discount_value)
    WHERE is_active = true;

-- ----------------------------------------------------------------------------
-- 3. Expression / Functional Indexes
-- ----------------------------------------------------------------------------

-- Case-insensitive customer authentication and lookup
CREATE INDEX IF NOT EXISTS idx_customers_lower_email
    ON customers (lower(email));

-- Case-insensitive SKU lookup for warehouse barcode scanners
CREATE INDEX IF NOT EXISTS idx_variants_lower_sku
    ON product_variants (lower(sku));

-- ----------------------------------------------------------------------------
-- 4. GIN (Generalized Inverted Index) for JSONB & Arrays
-- ----------------------------------------------------------------------------

-- JSONB containment queries on variant attributes (e.g., attributes @> '{"color": "Midnight Black"}')
-- jsonb_path_ops creates smaller, faster indexes tailored specifically for @> containment
CREATE INDEX IF NOT EXISTS idx_variants_attributes_gin
    ON product_variants USING gin (attributes jsonb_path_ops);

-- Array containment and overlap queries on product tags (e.g., tags && ARRAY['bluetooth', 'anc'])
CREATE INDEX IF NOT EXISTS idx_products_tags_gin
    ON products USING gin (tags);

-- JSONB geographical/zip routing queries on customer shipping address
CREATE INDEX IF NOT EXISTS idx_orders_shipping_address_gin
    ON orders USING gin (shipping_address jsonb_path_ops);
