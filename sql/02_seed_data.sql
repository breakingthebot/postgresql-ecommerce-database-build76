-- ============================================================================
-- PostgreSQL E-Commerce Database: Curated Seed Dataset
-- Version: 1.1.0
-- Purpose: Deterministic realistic relational data across all 12 schema tables
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. Brands
-- ----------------------------------------------------------------------------
INSERT INTO brands (id, name, slug, website, country) VALUES
(1, 'Apex Audio', 'apex-audio', 'https://apexaudio.example.com', 'US'),
(2, 'Volt Electronics', 'volt-electronics', 'https://voltelectronics.example.com', 'JP'),
(3, 'Nordic Wear', 'nordic-wear', 'https://nordicwear.example.com', 'SE'),
(4, 'Terra Outdoor', 'terra-outdoor', 'https://terraoutdoor.example.com', 'DE'),
(5, 'Lumina Home', 'lumina-home', 'https://luminahome.example.com', 'US')
ON CONFLICT (id) DO NOTHING;

-- ----------------------------------------------------------------------------
-- 2. Categories (Hierarchical Tree)
-- ----------------------------------------------------------------------------
INSERT INTO categories (id, parent_id, name, slug, description, hierarchy_path, depth, is_active) VALUES
(1, NULL, 'Electronics', 'electronics', 'Consumer electronics and smart gadgets', '/electronics', 0, true),
(2, 1, 'Audio & Sound', 'audio-sound', 'Headphones, earbuds, and premium speakers', '/electronics/audio-sound', 1, true),
(3, 2, 'Noise-Cancelling', 'noise-cancelling', 'Active noise cancelling headphones and headsets', '/electronics/audio-sound/noise-cancelling', 2, true),
(4, 1, 'Computers & Accessories', 'computers-accessories', 'Laptops, keyboards, and computer peripherals', '/electronics/computers-accessories', 1, true),
(5, NULL, 'Apparel & Fashion', 'apparel-fashion', 'Men and women outerwear and athletic clothing', '/apparel-fashion', 0, true),
(6, 5, 'Outerwear', 'outerwear', 'Jackets, coats, and weather-resistant gear', '/apparel-fashion/outerwear', 1, true),
(7, NULL, 'Home & Living', 'home-living', 'Modern home furnishings, lighting, and decor', '/home-living', 0, true)
ON CONFLICT (id) DO NOTHING;

-- ----------------------------------------------------------------------------
-- 3. Customers
-- ----------------------------------------------------------------------------
INSERT INTO customers (id, email, full_name, phone, role, is_active, metadata) VALUES
('11111111-1111-4111-a111-111111111111', 'elena.rostova@example.com', 'Elena Rostova', '+1-415-555-0101', 'customer', true, '{"tier": "vip", "referral": "organic"}'::jsonb),
('22222222-2222-4222-a222-222222222222', 'marcus.chen@example.com', 'Marcus Chen', '+1-206-555-0142', 'customer', true, '{"tier": "gold", "preferred_payment": "card"}'::jsonb),
('33333333-3333-4333-a333-333333333333', 'sarah.connor@example.com', 'Sarah Connor', '+1-310-555-0199', 'customer', true, '{"tier": "standard"}'::jsonb),
('44444444-4444-4444-a444-444444444444', 'admin.support@example.com', 'Devon Vance', '+1-800-555-0100', 'admin', true, '{"department": "ops"}'::jsonb)
ON CONFLICT (id) DO NOTHING;

-- ----------------------------------------------------------------------------
-- 4. Addresses
-- ----------------------------------------------------------------------------
INSERT INTO addresses (id, customer_id, type, recipient_name, street_line1, city, state, postal_code, country, is_default) VALUES
('a1111111-1111-4111-b111-111111111111', '11111111-1111-4111-a111-111111111111', 'both', 'Elena Rostova', '550 Montgomery St', 'San Francisco', 'CA', '94111', 'US', true),
('a2222222-2222-4222-b222-222222222222', '22222222-2222-4222-a222-222222222222', 'shipping', 'Marcus Chen', '1201 3rd Ave', 'Seattle', 'WA', '98101', 'US', true),
('a3333333-3333-4333-b333-333333333333', '33333333-3333-4333-a333-333333333333', 'both', 'Sarah Connor', '400 South Hope St', 'Los Angeles', 'CA', '90071', 'US', true)
ON CONFLICT (id) DO NOTHING;

-- ----------------------------------------------------------------------------
-- 5. Products
-- ----------------------------------------------------------------------------
INSERT INTO products (id, brand_id, category_id, name, slug, description, base_price, status, is_featured, tags, metadata) VALUES
(1, 1, 3, 'Apex Studio Pro ANC Headphones', 'apex-studio-pro-anc-headphones', 'Over-ear studio monitor headphones featuring hybrid 45dB active noise cancellation, 40mm beryllium drivers, and 60-hour battery life.', 349.99, 'active', true, ARRAY['audio', 'headphones', 'anc', 'bluetooth'], '{"warranty_years": 2, "water_resistance": "IPX4"}'::jsonb),
(2, 1, 2, 'Apex Wave True Wireless Earbuds', 'apex-wave-true-wireless-earbuds', 'Ultra-lightweight in-ear buds with spatial audio, transparency mode, and wireless charging case.', 179.99, 'active', true, ARRAY['audio', 'earbuds', 'wireless', 'bluetooth'], '{"warranty_years": 1, "water_resistance": "IPX7"}'::jsonb),
(3, 2, 4, 'Volt Mechanical Gaming Keyboard', 'volt-mechanical-gaming-keyboard', 'Customizable RGB hot-swappable mechanical keyboard with pre-lubed linear switches and aluminum chassis.', 149.50, 'active', false, ARRAY['gaming', 'keyboard', 'peripherals', 'mechanical'], '{"switch_type": "linear", "layout": "75%"}'::jsonb),
(4, 3, 6, 'Nordic Stormproof Expedition Parka', 'nordic-stormproof-expedition-parka', 'Triple-layer seam-sealed waterproof winter parka with recycled 800-fill down insulation and magnetic storm flap.', 495.00, 'active', true, ARRAY['apparel', 'winter', 'waterproof', 'jacket'], '{"temperature_rating": "-25C", "insulation": "800-fill down"}'::jsonb),
(5, 5, 7, 'Lumina Minimalist Smart Desk Lamp', 'lumina-minimalist-smart-desk-lamp', 'Circadian rhythm smart desk lamp with touch slide dimming, wireless phone charger base, and aluminum finish.', 89.00, 'active', false, ARRAY['home', 'lighting', 'smart-home', 'minimalist'], '{"color_temp": "2700K-6500K", "lumens": 800}'::jsonb)
ON CONFLICT (id) DO NOTHING;

-- ----------------------------------------------------------------------------
-- 6. Product Variants
-- ----------------------------------------------------------------------------
INSERT INTO product_variants (id, product_id, sku, barcode, attributes, price_override, weight_grams, is_active) VALUES
(1, 1, 'APX-ANC-BLK', '840123450011', '{"color": "Midnight Black", "finish": "Matte"}'::jsonb, 349.99, 280, true),
(2, 1, 'APX-ANC-SLV', '840123450012', '{"color": "Arctic Silver", "finish": "Brushed"}'::jsonb, 369.99, 280, true),
(3, 2, 'APX-WAV-WHT', '840123450021', '{"color": "Cloud White"}'::jsonb, 179.99, 45, true),
(4, 2, 'APX-WAV-BLK', '840123450022', '{"color": "Obsidian Black"}'::jsonb, 179.99, 45, true),
(5, 3, 'VLT-KB75-RED', '840123450031', '{"switch": "Red Linear", "keycaps": "PBT Double-Shot"}'::jsonb, 149.50, 950, true),
(6, 4, 'NOR-PRK-M-NVY', '840123450041', '{"size": "M", "color": "Navy Blue"}'::jsonb, 495.00, 1450, true),
(7, 4, 'NOR-PRK-L-NVY', '840123450042', '{"size": "L", "color": "Navy Blue"}'::jsonb, 495.00, 1500, true),
(8, 5, 'LUM-LMP-SLV', '840123450051', '{"finish": "Space Gray", "charger": "15W Qi"}'::jsonb, 89.00, 720, true)
ON CONFLICT (id) DO NOTHING;

-- ----------------------------------------------------------------------------
-- 7. Inventory
-- ----------------------------------------------------------------------------
INSERT INTO inventory (variant_id, warehouse_code, quantity_on_hand, quantity_reserved, reorder_point) VALUES
(1, 'WH-CENTRAL', 120, 15, 25),
(2, 'WH-CENTRAL', 85, 10, 20),
(3, 'WH-WEST', 200, 30, 40),
(4, 'WH-WEST', 175, 20, 35),
(5, 'WH-CENTRAL', 90, 8, 15),
(6, 'WH-NORTH', 45, 5, 10),
(7, 'WH-NORTH', 60, 12, 15),
(8, 'WH-CENTRAL', 110, 6, 20)
ON CONFLICT (variant_id) DO UPDATE SET
    quantity_on_hand = EXCLUDED.quantity_on_hand,
    quantity_reserved = EXCLUDED.quantity_reserved;

-- ----------------------------------------------------------------------------
-- 8. Coupons
-- ----------------------------------------------------------------------------
INSERT INTO coupons (id, code, discount_type, discount_value, min_order_value, max_uses, uses_count, valid_from, valid_until, is_active) VALUES
(1, 'WELCOME20', 'percentage', 20.00, 100.00, 1000, 42, clock_timestamp() - INTERVAL '30 days', clock_timestamp() + INTERVAL '60 days', true),
(2, 'SUMMER50', 'fixed', 50.00, 250.00, 500, 118, clock_timestamp() - INTERVAL '15 days', clock_timestamp() + INTERVAL '45 days', true),
(3, 'VIP10', 'percentage', 10.00, 50.00, NULL, 340, clock_timestamp() - INTERVAL '60 days', clock_timestamp() + INTERVAL '120 days', true)
ON CONFLICT (id) DO NOTHING;

-- ----------------------------------------------------------------------------
-- 9. Orders
-- ----------------------------------------------------------------------------
INSERT INTO orders (id, customer_id, coupon_id, order_number, status, subtotal, discount_amount, tax_amount, shipping_fee, total_amount, shipping_address, billing_address, payment_method, placed_at) VALUES
('e1111111-1111-4111-c111-111111111111', '11111111-1111-4111-a111-111111111111', 1, 'ORD-2026-1001', 'delivered', 529.98, 105.99, 38.16, 0.00, 462.15,
 '{"name": "Elena Rostova", "street": "550 Montgomery St", "city": "San Francisco", "state": "CA", "zip": "94111"}'::jsonb,
 '{"name": "Elena Rostova", "street": "550 Montgomery St", "city": "San Francisco", "state": "CA", "zip": "94111"}'::jsonb,
 'credit_card', clock_timestamp() - INTERVAL '14 days'),

('e2222222-2222-4222-c222-222222222222', '22222222-2222-4222-a222-222222222222', 2, 'ORD-2026-1002', 'shipped', 495.00, 50.00, 40.05, 15.00, 500.05,
 '{"name": "Marcus Chen", "street": "1201 3rd Ave", "city": "Seattle", "state": "WA", "zip": "98101"}'::jsonb,
 '{"name": "Marcus Chen", "street": "1201 3rd Ave", "city": "Seattle", "state": "WA", "zip": "98101"}'::jsonb,
 'apple_pay', clock_timestamp() - INTERVAL '3 days'),

('e3333333-3333-4333-c333-333333333333', '33333333-3333-4333-a333-333333333333', NULL, 'ORD-2026-1003', 'paid', 238.50, 0.00, 19.08, 0.00, 257.58,
 '{"name": "Sarah Connor", "street": "400 South Hope St", "city": "Los Angeles", "state": "CA", "zip": "90071"}'::jsonb,
 '{"name": "Sarah Connor", "street": "400 South Hope St", "city": "Los Angeles", "state": "CA", "zip": "90071"}'::jsonb,
 'paypal', clock_timestamp() - INTERVAL '1 day')
ON CONFLICT (id) DO NOTHING;

-- ----------------------------------------------------------------------------
-- 10. Order Items
-- ----------------------------------------------------------------------------
INSERT INTO order_items (id, order_id, variant_id, product_name_snapshot, sku_snapshot, unit_price, quantity, line_total) VALUES
(1, 'e1111111-1111-4111-c111-111111111111', 1, 'Apex Studio Pro ANC Headphones', 'APX-ANC-BLK', 349.99, 1, 349.99),
(2, 'e1111111-1111-4111-c111-111111111111', 3, 'Apex Wave True Wireless Earbuds', 'APX-WAV-WHT', 179.99, 1, 179.99),
(3, 'e2222222-2222-4222-c222-222222222222', 6, 'Nordic Stormproof Expedition Parka', 'NOR-PRK-M-NVY', 495.00, 1, 495.00),
(4, 'e3333333-3333-4333-c333-333333333333', 5, 'Volt Mechanical Gaming Keyboard', 'VLT-KB75-RED', 149.50, 1, 149.50),
(5, 'e3333333-3333-4333-c333-333333333333', 8, 'Lumina Minimalist Smart Desk Lamp', 'LUM-LMP-SLV', 89.00, 1, 89.00)
ON CONFLICT (id) DO NOTHING;

-- ----------------------------------------------------------------------------
-- 11. Order Status History
-- ----------------------------------------------------------------------------
INSERT INTO order_status_history (id, order_id, from_status, to_status, change_reason, changed_by, changed_at) VALUES
(1, 'e1111111-1111-4111-c111-111111111111', NULL, 'pending', 'Customer checkout initiated', 'system', clock_timestamp() - INTERVAL '14 days'),
(2, 'e1111111-1111-4111-c111-111111111111', 'pending', 'paid', 'Payment authorized and captured', 'stripe_webhook', clock_timestamp() - INTERVAL '14 days' + INTERVAL '2 minutes'),
(3, 'e1111111-1111-4111-c111-111111111111', 'paid', 'shipped', 'Dispatched via FedEx Express', 'warehouse_lead', clock_timestamp() - INTERVAL '13 days'),
(4, 'e1111111-1111-4111-c111-111111111111', 'shipped', 'delivered', 'Signed by recipient', 'fedex_carrier', clock_timestamp() - INTERVAL '10 days'),
(5, 'e2222222-2222-4222-c222-222222222222', NULL, 'pending', 'Customer checkout initiated', 'system', clock_timestamp() - INTERVAL '3 days'),
(6, 'e2222222-2222-4222-c222-222222222222', 'pending', 'paid', 'Apple Pay authorized', 'apple_pay_gw', clock_timestamp() - INTERVAL '3 days' + INTERVAL '1 minute'),
(7, 'e2222222-2222-4222-c222-222222222222', 'paid', 'shipped', 'Dispatched via UPS Ground', 'warehouse_lead', clock_timestamp() - INTERVAL '2 days'),
(8, 'e3333333-3333-4333-c333-333333333333', NULL, 'pending', 'Customer checkout initiated', 'system', clock_timestamp() - INTERVAL '1 day'),
(9, 'e3333333-3333-4333-c333-333333333333', 'pending', 'paid', 'PayPal settlement confirmed', 'paypal_ipn', clock_timestamp() - INTERVAL '1 day' + INTERVAL '3 minutes')
ON CONFLICT (id) DO NOTHING;

-- ----------------------------------------------------------------------------
-- 12. Reviews
-- ----------------------------------------------------------------------------
INSERT INTO reviews (id, product_id, customer_id, rating, title, body, is_verified_purchase, helpful_votes) VALUES
(1, 1, '11111111-1111-4111-a111-111111111111', 5, 'Unmatched acoustic clarity and ANC', 'The noise cancellation completely silences subway commutes. Battery easily lasts the entire work week on a single charge.', true, 48),
(2, 2, '11111111-1111-4111-a111-111111111111', 4, 'Great fit and punchy bass', 'Extremely comfortable for running. Transparency mode sounds completely natural without robotic artifacts.', true, 19),
(3, 4, '22222222-2222-4222-a222-222222222222', 5, 'Indispensable winter armor', 'Survived sub-zero blizzards in Alaska while staying totally toasty and dry. Worth every single penny.', true, 34),
(4, 3, '33333333-3333-4333-a333-333333333333', 5, 'Silky smooth typing experience', 'The factory pre-lubed switches sound thocky right out of the box. Zero ping and great Bluetooth latency.', true, 12)
ON CONFLICT (id) DO NOTHING;
