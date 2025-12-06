#!/usr/bin/env python3
"""
Flask Integration Example - sqlalchemy-engine-kit

Bu örnek, Flask uygulamasında sqlalchemy-engine-kit kullanımını gösterir.
"""

from flask import Flask, jsonify, request
from sqlalchemy_engine_kit import (
    DatabaseManager,
    get_sqlite_config,
    with_session,
    with_readonly_session,
    Base,
    TimestampMixin,
)
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import Session

app = Flask(__name__)


# Model
class Product(Base, TimestampMixin):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    price = Column(Float, nullable=False)
    description = Column(String(500))


# Database initialization
def init_app():
    """Flask uygulamasını başlat."""
    import os
    db_file = "flask_example.db"
    # Önceki database dosyasını sil (temiz başlangıç için)
    if os.path.exists(db_file):
        os.remove(db_file)
    
    config = get_sqlite_config(db_file)
    manager = DatabaseManager()
    manager.initialize(config, auto_start=True)
    Base.metadata.create_all(manager.engine._engine)
    print("✅ Database initialized for Flask app")
    return manager


# Initialize database
db_manager = init_app()


# Routes
@app.route('/products', methods=['GET'])
@with_readonly_session()
def list_products(session: Session):
    """Tüm ürünleri listele."""
    products = session.query(Product).all()
    return jsonify([
        {
            'id': p.id,
            'name': p.name,
            'price': float(p.price),
            'description': p.description
        }
        for p in products
    ])


@app.route('/products', methods=['POST'])
@with_session()
def create_product(session: Session):
    """Yeni ürün oluştur."""
    data = request.json
    product = Product(
        name=data['name'],
        price=data['price'],
        description=data.get('description', '')
    )
    session.add(product)
    session.flush()
    
    return jsonify({
        'id': product.id,
        'name': product.name,
        'price': float(product.price),
        'description': product.description
    }), 201


@app.route('/products/<int:product_id>', methods=['GET'])
@with_readonly_session()
def get_product(session: Session, product_id: int):
    """Ürün getir."""
    product = session.query(Product).filter_by(id=product_id).first()
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    return jsonify({
        'id': product.id,
        'name': product.name,
        'price': float(product.price),
        'description': product.description
    })


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    health = db_manager.engine.health_check()
    return jsonify(health), 200 if health['status'] == 'healthy' else 503


if __name__ == '__main__':
    print("=" * 60)
    print("Flask Integration Example")
    print("=" * 60)
    print("\nStarting Flask app on http://127.0.0.1:5000")
    print("\nEndpoints:")
    print("  GET  /products          - List all products")
    print("  POST /products          - Create product")
    print("  GET  /products/<id>     - Get product")
    print("  GET  /health            - Health check")
    print("\nExample POST request:")
    print('  curl -X POST http://127.0.0.1:5000/products \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"name": "Laptop", "price": 999.99, "description": "Gaming laptop"}\'')
    print("\n" + "=" * 60)
    
    app.run(debug=True, port=5000)

