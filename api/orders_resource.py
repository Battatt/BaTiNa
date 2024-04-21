import data
from data.order import Order
from flask_restful import Resource
from flask import jsonify
import logging

logging.basicConfig(level=logging.INFO, filename="py_log.log",filemode="w",
                    format="%(asctime)s %(levelname)s %(message)s")


class OrdersResource(Resource):
    def get(self, id: int):
        if abort_if_order_is_not_found(id):
            return jsonify({'status': f"Item {id} not found"})
        session = data.db_session.create_session()
        orders = session.query(data.order.Order).filter(data.order.Order.id == id).first()  # type:ignore[call-arg]
        return jsonify({'user': {'id': orders.id, 'name': orders.name,'customer': orders.customer,
                                 'content': orders.content, 'date': orders.date, 'is_finished': orders.is_finished}})

    def delete(self, id: int):
        if abort_if_order_is_not_found(id):
            return jsonify({'status': f"Item {id} not found"})
        session = data.db_session.create_session()
        orders = session.query(data.order.Order).filter(data.order.Order.id == id).first()  # type:ignore[call-arg]
        session.delete(orders)
        session.commit()
        return jsonify({'success': 'OK'})


class OrdersList(Resource):
    def get(self):
        session = data.db_session.create_session()
        orders = session.query(Order).all()
        orders_list = []
        for order in orders:
            order_dict = order.to_dict(
                only=('id', 'customer', 'name', 'content', 'date', 'is_finished'))
            orders_list.append(order_dict)
        return jsonify({'orders': orders_list})


def abort_if_order_is_not_found(id):
    session = data.db_session.create_session()
    orders = session.query(data.order.Order).filter(data.order.Order.id == id).first()  # type:ignore[call-arg]
    if not orders:
        return True
