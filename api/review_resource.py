import data
from data.review import Review
from flask_restful import Resource
from flask import jsonify
import logging
import base64

logging.basicConfig(level=logging.INFO, filename="py_log.log",filemode="w",
                    format="%(asctime)s %(levelname)s %(message)s")


class ReviewResource(Resource):
    def get(self, id: int):
        if abort_if_review_is_not_found(id):
            return jsonify({'status': f"Review {id} not found"})
        session = data.db_session.create_session()
        reviews = session.query(data.review.Review).filter(data.review.Review.id == id).first()  # type:ignore[call-arg]
        return jsonify({'user': {'id': reviews.id, 'customer': reviews.customer, 'item_id': reviews.item_id,
                                 'name': reviews.name, 'text': reviews.text, 'date': reviews.date,
                                 'avatar': reviews.avatar}})

    def delete(self, id: int):
        if abort_if_review_is_not_found(id):
            return jsonify({'status': f"Review {id} not found"})
        session = data.db_session.create_session()
        reviews = session.query(data.review.Review).filter(data.review.Review.id == id).first()  # type:ignore[call-arg]
        session.delete(reviews)
        session.commit()
        return jsonify({'success': 'OK'})


class ReviewListResource(Resource):
    def get(self):
        session = data.db_session.create_session()
        reviews = session.query(Review).all()
        reviews_list = []
        for review in reviews:
            review_dict = review.to_dict(
                only=('id', 'customer', 'name', 'item_id', 'text', 'date', 'avatar'))
            review_dict["avatar"] = review.avatar
            review_dict["avatar"] = review_dict["avatar"]
            reviews_list.append(review_dict)
        return jsonify({'reviews': reviews_list})


def abort_if_review_is_not_found(id):
    session = data.db_session.create_session()
    reviews = session.query(data.item.Item).filter(data.review.Review.id == id).first()  # type:ignore[call-arg]
    if not reviews:
        return True
