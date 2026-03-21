# Chạy thử
from logic_xu_ly.supplier_db import add_supplier
from logic_xu_ly.customer_db import add_customer
from logic_xu_ly.product_db import add_product

# Dữ liệu supplier mẫu
add_supplier("Tech Supplies Co.", "Electronics", "john@techsupplies.com", "+1 (555) 123-4567", "123 Tech Street, Silicon Valley", "John Smith")
add_supplier("Office Depot", "Office Supplies", "sarah@officedepot.com", "+1 (555) 234-5678", "456 Office Ave, New York", "Sarah Johnson")

# Dữ liệu customer mẫu
add_customer("ABC Corporation", "contact@abc.com", "+1 (555) 123-4567", 45, 12450, "active")
add_customer("XYZ Industries", "info@xyz.com", "+1 (555) 234-5678", 32, 8320, "active")

# Dữ liệu product mẫu
add_product("PROD-001", "Wireless Mouse", "Electronics", 245, 29.99, 15.00, "in stock")
add_product("PROD-002", "USB-C Cable", "Accessories", 12, 12.99, 6.50, "low stock")

print("Dữ liệu mẫu đã sẵn sàng trong logic_xu_ly/inventory.db!")