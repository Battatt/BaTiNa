import data
from data.item import Item
from flask_restful import Resource
from flask import jsonify
import logging
import base64

logging.basicConfig(level=logging.INFO, filename="py_log.log",filemode="w",
                    format="%(asctime)s %(levelname)s %(message)s")


class ItemResource(Resource):
    def get(self, id: int):
        if abort_if_item_is_not_found(id):
            return jsonify({'status': f"Item {id} not found"})
        session = data.db_session.create_session()
        items = session.query(data.item.Item).filter(data.item.Item.id == id).first()  # type:ignore[call-arg]
        return jsonify({'user': {'id': items.id, 'seller_id': items.seller_id, 'name': items.name,
                                 'description': items.description,
                                 'price': items.price, 'image': items.image.hex(), 'amount': items.amount,
                                 'category': items.category, 'is_visible': items.is_visible}})

    def delete(self, id: int):
        if abort_if_item_is_not_found(id):
            return jsonify({'status': f"Item {id} not found"})
        session = data.db_session.create_session()
        items = session.query(data.item.Item).filter(data.item.Item.id == id).first()  # type:ignore[call-arg]
        session.delete(items)
        session.commit()
        return jsonify({'success': 'OK'})


class ItemListResource(Resource):
    def get(self):
        session = data.db_session.create_session()
        items = session.query(Item).all()
        items_list = []
        for item in items:
            item_dict = item.to_dict(
                only=('id', 'seller_id', 'name', 'price', 'amount', 'description', 'is_visible', 'category'))
            item_dict["image"] = item.image.hex()
            item_dict["image"] = base64.b64encode(bytes.fromhex(item_dict["image"])).decode('ascii')
            items_list.append(item_dict)
        return jsonify({'items': items_list})


def abort_if_item_is_not_found(id):
    session = data.db_session.create_session()
    items = session.query(data.item.Item).filter(data.item.Item.id == id).first()  # type:ignore[call-arg]
    if not items:
        return True
