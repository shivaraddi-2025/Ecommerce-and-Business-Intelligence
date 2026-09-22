CREATE DATABASE IF NOT EXISTS ecommerce_intelligence;
USE ecommerce_intelligence;

CREATE TABLE customers (customer_id VARCHAR(32) PRIMARY KEY, customer_name VARCHAR(150), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE categories (category_id INT AUTO_INCREMENT PRIMARY KEY, category_name VARCHAR(80) UNIQUE NOT NULL);
CREATE TABLE products (product_id VARCHAR(64) PRIMARY KEY, product_name VARCHAR(180) NOT NULL, category_id INT NOT NULL, sub_category VARCHAR(80), FOREIGN KEY (category_id) REFERENCES categories(category_id));
CREATE TABLE locations (location_id INT AUTO_INCREMENT PRIMARY KEY, region VARCHAR(80) NOT NULL, state VARCHAR(80) NOT NULL, city VARCHAR(100) NOT NULL, UNIQUE(region, state, city));
CREATE TABLE orders (order_id VARCHAR(40) PRIMARY KEY, order_date DATE NOT NULL, customer_id VARCHAR(32) NOT NULL, location_id INT NOT NULL, shipping_mode VARCHAR(40) NOT NULL, FOREIGN KEY (customer_id) REFERENCES customers(customer_id), FOREIGN KEY (location_id) REFERENCES locations(location_id), INDEX(order_date));
CREATE TABLE order_items (order_item_id BIGINT AUTO_INCREMENT PRIMARY KEY, order_id VARCHAR(40) NOT NULL, product_id VARCHAR(64) NOT NULL, quantity INT NOT NULL, sales DECIMAL(14,2) NOT NULL, profit DECIMAL(14,2) NOT NULL, discount DECIMAL(5,4), FOREIGN KEY (order_id) REFERENCES orders(order_id), FOREIGN KEY (product_id) REFERENCES products(product_id), INDEX(product_id));
CREATE TABLE returns (order_id VARCHAR(40) PRIMARY KEY, return_status ENUM('Returned','Not Returned') NOT NULL, FOREIGN KEY (order_id) REFERENCES orders(order_id));

CREATE OR REPLACE VIEW monthly_sales AS SELECT DATE_FORMAT(o.order_date,'%Y-%m') AS month, SUM(i.sales) AS sales, SUM(i.profit) AS profit, COUNT(DISTINCT o.order_id) AS orders FROM orders o JOIN order_items i ON i.order_id=o.order_id GROUP BY month;
CREATE OR REPLACE VIEW category_performance AS SELECT p.category_id, SUM(i.sales) AS sales, SUM(i.profit) AS profit, SUM(i.quantity) AS units FROM products p JOIN order_items i ON i.product_id=p.product_id GROUP BY p.category_id;
